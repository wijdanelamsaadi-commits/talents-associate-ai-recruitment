<?php
/**
 * Plugin Name: Talents Associate WordPress Bridge
 * Description: Sends the public recruitment form to the Talents Associate FastAPI backend with a temporary email fallback.
 * Version: 0.1.0
 * Author: Talents Associate
 */

if (!defined('ABSPATH')) {
    exit;
}

const TALENTS_BRIDGE_NONCE_ACTION = 'talents_send_job_form';
const TALENTS_BRIDGE_NONCE_FIELD = 'talents_nonce';
const TALENTS_BRIDGE_MAX_CV_BYTES = 5242880; // 5 MB, aligned with the current FastAPI backend.
const TALENTS_BRIDGE_FALLBACK_EMAIL = 'Recrutement@talentsag.ma';

add_action('wp_loaded', 'talents_bridge_register_ajax_handlers', 1000);
add_action('wp_enqueue_scripts', 'talents_bridge_enqueue_form_script');

/**
 * Ensure one AJAX handler answers send_job_form.
 *
 * The old theme email function remains in functions.php for rollback, but its
 * hooks are removed at runtime to avoid double submissions while this bridge is active.
 */
function talents_bridge_register_ajax_handlers(): void
{
    remove_all_actions('wp_ajax_send_job_form');
    remove_all_actions('wp_ajax_nopriv_send_job_form');

    add_action('wp_ajax_send_job_form', 'talents_send_job_form');
    add_action('wp_ajax_nopriv_send_job_form', 'talents_send_job_form');
}

function talents_bridge_enqueue_form_script(): void
{
    wp_register_script('talents-wordpress-bridge', '', array(), '0.1.0', true);
    wp_enqueue_script('talents-wordpress-bridge');
    wp_localize_script(
        'talents-wordpress-bridge',
        'TalentsBridge',
        array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce(TALENTS_BRIDGE_NONCE_ACTION),
            'nonceField' => TALENTS_BRIDGE_NONCE_FIELD,
            'action' => 'send_job_form',
            'loadingText' => 'Envoi en cours...',
            'successText' => 'Votre candidature a bien été reçue.',
            'genericError' => 'Votre candidature n’a pas pu être envoyée. Veuillez réessayer.',
        )
    );

    wp_add_inline_script('talents-wordpress-bridge', talents_bridge_elementor_javascript());
}

function talents_send_job_form(): void
{
    $request_id = talents_bridge_request_id();

    if (!talents_bridge_verify_nonce()) {
        talents_bridge_log('nonce_invalid', $request_id, 403);
        wp_send_json_error(array('message' => 'Session expirée. Veuillez actualiser la page puis réessayer.'), 403);
    }

    if (!defined('TALENTS_FASTAPI_URL') || !defined('TALENTS_FASTAPI_KEY') || TALENTS_FASTAPI_URL === '' || TALENTS_FASTAPI_KEY === '') {
        talents_bridge_log('config_missing', $request_id, 500);
        wp_send_json_error(array('message' => 'Le service de candidature n’est pas encore configuré.'), 500);
    }

    $validation = talents_bridge_validate_request();
    if (!$validation['valid']) {
        talents_bridge_log('validation_failed', $request_id, 400);
        wp_send_json_error(array('message' => $validation['message']), 400);
    }

    $fields = $validation['fields'];
    $file = $validation['file'];
    $api_response = talents_bridge_send_to_fastapi($fields, $file, $request_id);

    if ($api_response['success']) {
        wp_send_json_success(array('message' => 'Votre candidature a bien été reçue.'));
    }

    if ($api_response['fallback_allowed']) {
        $fallback_sent = talents_bridge_send_fallback_email($fields, $file, $request_id);
        if ($fallback_sent) {
            wp_send_json_success(array('message' => 'Votre candidature a bien été reçue.'));
        }
        wp_send_json_error(
            array('message' => 'Le service de candidature est momentanément indisponible. Veuillez réessayer plus tard.'),
            503
        );
    }

    wp_send_json_error(
        array('message' => $api_response['message'] ?: 'Votre candidature contient une erreur. Veuillez vérifier les informations saisies.'),
        $api_response['status_code'] ?: 400
    );
}

function talents_bridge_verify_nonce(): bool
{
    $nonce = '';
    if (isset($_POST[TALENTS_BRIDGE_NONCE_FIELD])) {
        $nonce = sanitize_text_field(wp_unslash($_POST[TALENTS_BRIDGE_NONCE_FIELD]));
    } elseif (isset($_POST['nonce'])) {
        $nonce = sanitize_text_field(wp_unslash($_POST['nonce']));
    }

    return $nonce !== '' && wp_verify_nonce($nonce, TALENTS_BRIDGE_NONCE_ACTION) !== false;
}

function talents_bridge_validate_request(): array
{
    $fields = array(
        'opportunite' => talents_bridge_post_text('opportunite'),
        'nom' => talents_bridge_post_text('nom'),
        'prenom' => talents_bridge_post_text('prenom'),
        'email' => sanitize_email(talents_bridge_post_text('email')),
        'telephone' => talents_bridge_post_text('telephone'),
        'ville' => talents_bridge_post_text('ville'),
        'message' => talents_bridge_post_textarea('message'),
    );

    foreach (array('opportunite', 'nom', 'prenom', 'email', 'ville') as $required_field) {
        if ($fields[$required_field] === '') {
            return array('valid' => false, 'message' => 'Veuillez compléter tous les champs obligatoires.');
        }
    }

    if (!is_email($fields['email'])) {
        return array('valid' => false, 'message' => 'Veuillez saisir une adresse e-mail valide.');
    }

    if (!isset($_FILES['cv']) || !is_array($_FILES['cv'])) {
        return array('valid' => false, 'message' => 'Veuillez ajouter votre CV au format PDF ou DOCX.');
    }

    $file = $_FILES['cv'];
    if (!empty($file['error'])) {
        return array('valid' => false, 'message' => talents_bridge_upload_error_message((int) $file['error']));
    }

    if (empty($file['tmp_name']) || !is_uploaded_file($file['tmp_name'])) {
        return array('valid' => false, 'message' => 'Le fichier CV est introuvable. Veuillez réessayer.');
    }

    if ((int) $file['size'] <= 0) {
        return array('valid' => false, 'message' => 'Le fichier CV est vide.');
    }

    if ((int) $file['size'] > TALENTS_BRIDGE_MAX_CV_BYTES) {
        return array('valid' => false, 'message' => 'Le CV dépasse la taille maximale autorisée de 5 Mo.');
    }

    $filename = sanitize_file_name((string) $file['name']);
    $allowed_mimes = array(
        'pdf' => 'application/pdf',
        'docx' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    );
    $checked = wp_check_filetype_and_ext($file['tmp_name'], $filename, $allowed_mimes);
    $extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    if (!in_array($extension, array('pdf', 'docx'), true) || empty($checked['ext'])) {
        return array('valid' => false, 'message' => 'Format de CV non autorisé. Importez un fichier PDF ou DOCX.');
    }

    if (function_exists('finfo_open')) {
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mime = $finfo ? finfo_file($finfo, $file['tmp_name']) : '';
        if ($finfo) {
            finfo_close($finfo);
        }
        $valid_mimes = array_values($allowed_mimes);
        $zip_docx_mime = 'application/zip';
        if ($mime && !in_array($mime, $valid_mimes, true) && !($extension === 'docx' && $mime === $zip_docx_mime)) {
            return array('valid' => false, 'message' => 'Le type réel du fichier CV n’est pas autorisé.');
        }
    }

    $file['name'] = $filename;
    return array('valid' => true, 'fields' => $fields, 'file' => $file);
}

function talents_bridge_send_to_fastapi(array $fields, array $file, string $request_id): array
{
    if (function_exists('curl_init')) {
        return talents_bridge_send_with_curl($fields, $file, $request_id);
    }

    return talents_bridge_send_with_wp_http($fields, $file, $request_id);
}

function talents_bridge_send_with_curl(array $fields, array $file, string $request_id): array
{
    $curl = curl_init((string) TALENTS_FASTAPI_URL);
    $payload = $fields;
    $payload['cv'] = new CURLFile($file['tmp_name'], (string) $file['type'], (string) $file['name']);

    curl_setopt_array(
        $curl,
        array(
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_HTTPHEADER => array(
                'X-Talents-Api-Key: ' . TALENTS_FASTAPI_KEY,
                'X-Talents-Request-Id: ' . $request_id,
            ),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 60,
        )
    );

    $body = curl_exec($curl);
    $error = curl_error($curl);
    $status_code = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    curl_close($curl);

    if ($body === false) {
        talents_bridge_log('curl_error', $request_id, 0);
        return talents_bridge_api_result(false, 0, 'Le service de candidature est indisponible.', true);
    }

    return talents_bridge_parse_api_response((string) $body, $status_code, $request_id);
}

function talents_bridge_send_with_wp_http(array $fields, array $file, string $request_id): array
{
    $boundary = 'talents-' . wp_generate_uuid4();
    $body = talents_bridge_build_multipart_body($fields, $file, $boundary);
    $response = wp_remote_post(
        (string) TALENTS_FASTAPI_URL,
        array(
            'timeout' => 60,
            'headers' => array(
                'Content-Type' => 'multipart/form-data; boundary=' . $boundary,
                'X-Talents-Api-Key' => (string) TALENTS_FASTAPI_KEY,
                'X-Talents-Request-Id' => $request_id,
            ),
            'body' => $body,
        )
    );

    if (is_wp_error($response)) {
        talents_bridge_log('wp_http_error', $request_id, 0);
        return talents_bridge_api_result(false, 0, 'Le service de candidature est indisponible.', true);
    }

    return talents_bridge_parse_api_response(
        (string) wp_remote_retrieve_body($response),
        (int) wp_remote_retrieve_response_code($response),
        $request_id
    );
}

function talents_bridge_parse_api_response(string $body, int $status_code, string $request_id): array
{
    $decoded = json_decode($body, true);
    $success = $status_code >= 200 && $status_code < 300 && is_array($decoded) && !empty($decoded['success']);

    talents_bridge_log($success ? 'api_success' : 'api_error', $request_id, $status_code);

    if ($success) {
        return talents_bridge_api_result(true, $status_code, 'Votre candidature a bien été reçue.', false);
    }

    $fallback_allowed = $status_code === 0 || $status_code >= 500;
    $message = 'Votre candidature n’a pas pu être envoyée.';
    if (is_array($decoded) && !empty($decoded['detail']) && !$fallback_allowed) {
        $message = is_string($decoded['detail']) ? $decoded['detail'] : 'Veuillez vérifier les informations saisies.';
    }

    return talents_bridge_api_result(false, $status_code, $message, $fallback_allowed);
}

function talents_bridge_build_multipart_body(array $fields, array $file, string $boundary): string
{
    $eol = "\r\n";
    $body = '';
    foreach ($fields as $name => $value) {
        $body .= '--' . $boundary . $eol;
        $body .= 'Content-Disposition: form-data; name="' . $name . '"' . $eol . $eol;
        $body .= (string) $value . $eol;
    }
    $body .= '--' . $boundary . $eol;
    $body .= 'Content-Disposition: form-data; name="cv"; filename="' . $file['name'] . '"' . $eol;
    $body .= 'Content-Type: ' . ($file['type'] ?: 'application/octet-stream') . $eol . $eol;
    $body .= file_get_contents($file['tmp_name']) . $eol;
    $body .= '--' . $boundary . '--' . $eol;
    return $body;
}

function talents_bridge_send_fallback_email(array $fields, array $file, string $request_id): bool
{
    $subject = 'Nouvelle candidature Talents Associate';
    $body = "Une candidature a été reçue depuis le formulaire WordPress.\n\n";
    $body .= 'Opportunité : ' . $fields['opportunite'] . "\n";
    $body .= 'Nom : ' . $fields['nom'] . "\n";
    $body .= 'Prénom : ' . $fields['prenom'] . "\n";
    $body .= 'Email : ' . $fields['email'] . "\n";
    $body .= 'Téléphone : ' . $fields['telephone'] . "\n";
    $body .= 'Ville : ' . $fields['ville'] . "\n";
    $body .= "\nMessage :\n" . $fields['message'] . "\n";
    $headers = array('Content-Type: text/plain; charset=UTF-8');
    $sent = wp_mail(TALENTS_BRIDGE_FALLBACK_EMAIL, $subject, $body, $headers, array($file['tmp_name']));
    talents_bridge_log($sent ? 'fallback_email_sent' : 'fallback_email_failed', $request_id, $sent ? 200 : 500);
    return (bool) $sent;
}

function talents_bridge_api_result(bool $success, int $status_code, string $message, bool $fallback_allowed): array
{
    return array(
        'success' => $success,
        'status_code' => $status_code,
        'message' => $message,
        'fallback_allowed' => $fallback_allowed,
    );
}

function talents_bridge_post_text(string $field): string
{
    return isset($_POST[$field]) ? sanitize_text_field(wp_unslash($_POST[$field])) : '';
}

function talents_bridge_post_textarea(string $field): string
{
    return isset($_POST[$field]) ? sanitize_textarea_field(wp_unslash($_POST[$field])) : '';
}

function talents_bridge_upload_error_message(int $error_code): string
{
    $messages = array(
        UPLOAD_ERR_INI_SIZE => 'Le fichier dépasse la taille autorisée par le serveur.',
        UPLOAD_ERR_FORM_SIZE => 'Le fichier dépasse la taille autorisée par le formulaire.',
        UPLOAD_ERR_PARTIAL => 'Le fichier CV n’a été chargé que partiellement.',
        UPLOAD_ERR_NO_FILE => 'Veuillez ajouter votre CV.',
        UPLOAD_ERR_NO_TMP_DIR => 'Le serveur ne peut pas recevoir le fichier temporaire.',
        UPLOAD_ERR_CANT_WRITE => 'Le serveur ne peut pas enregistrer le fichier temporaire.',
        UPLOAD_ERR_EXTENSION => 'Le chargement du fichier a été bloqué par le serveur.',
    );
    return $messages[$error_code] ?? 'Le fichier CV n’a pas pu être chargé.';
}

function talents_bridge_request_id(): string
{
    return wp_generate_uuid4();
}

function talents_bridge_log(string $event, string $request_id, int $status_code): void
{
    error_log(sprintf('[talents-wordpress-bridge] event=%s request_id=%s status=%d', $event, $request_id, $status_code));
}

function talents_bridge_elementor_javascript(): string
{
    return <<<'JS'
(function () {
  function findForm() {
    return document.querySelector('form[data-talents-job-form="true"]') ||
      document.querySelector('#talents-job-form') ||
      document.querySelector('form.talents-job-form');
  }

  function setMessage(form, text, type) {
    var messageBox = form.querySelector('[data-talents-form-message]');
    if (!messageBox) {
      messageBox = document.createElement('div');
      messageBox.setAttribute('data-talents-form-message', 'true');
      messageBox.style.marginTop = '12px';
      form.appendChild(messageBox);
    }
    messageBox.textContent = text;
    messageBox.style.color = type === 'success' ? '#047857' : '#b91c1c';
  }

  function getField(form, name) {
    return form.querySelector('[name="' + name + '"]');
  }

  function bindForm(form) {
    if (!form || form.dataset.talentsBridgeBound === 'true') {
      return;
    }
    form.dataset.talentsBridgeBound = 'true';

    form.addEventListener('submit', function (event) {
      event.preventDefault();

      var submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitButton && submitButton.disabled) {
        return;
      }

      var cvField = getField(form, 'cv');
      if (!cvField || !cvField.files || !cvField.files.length) {
        setMessage(form, 'Veuillez ajouter votre CV au format PDF ou DOCX.', 'error');
        return;
      }

      var formData = new FormData(form);
      formData.set('action', TalentsBridge.action);
      formData.set(TalentsBridge.nonceField, TalentsBridge.nonce);

      var previousLabel = submitButton ? (submitButton.value || submitButton.textContent) : '';
      if (submitButton) {
        submitButton.disabled = true;
        if ('value' in submitButton) {
          submitButton.value = TalentsBridge.loadingText;
        } else {
          submitButton.textContent = TalentsBridge.loadingText;
        }
      }

      fetch(TalentsBridge.ajaxUrl, {
        method: 'POST',
        credentials: 'same-origin',
        body: formData
      })
        .then(function (response) {
          return response.json().then(function (payload) {
            return { ok: response.ok, payload: payload };
          });
        })
        .then(function (result) {
          var payload = result.payload || {};
          var message = payload.data && payload.data.message ? payload.data.message : TalentsBridge.genericError;
          if (payload.success) {
            setMessage(form, message || TalentsBridge.successText, 'success');
            form.reset();
          } else {
            setMessage(form, message, 'error');
          }
        })
        .catch(function () {
          setMessage(form, TalentsBridge.genericError, 'error');
        })
        .finally(function () {
          if (submitButton) {
            submitButton.disabled = false;
            if ('value' in submitButton) {
              submitButton.value = previousLabel;
            } else {
              submitButton.textContent = previousLabel;
            }
          }
        });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindForm(findForm());
  });
})();
JS;
}
