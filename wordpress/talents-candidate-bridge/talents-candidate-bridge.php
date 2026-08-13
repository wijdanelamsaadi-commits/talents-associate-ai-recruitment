<?php
/**
 * Plugin Name: Talents Candidate Bridge
 * Description: Affiche les offres publiques et envoie les candidatures vers l'API Talents Associate.
 * Version: 1.2.0
 * Author: Talents Associate
 * Text Domain: talents-candidate-bridge
 */

if (!defined('ABSPATH')) {
    exit;
}

const TALENTS_CANDIDATE_BRIDGE_VERSION = '1.2.0';
const TALENTS_CANDIDATE_BRIDGE_OPTION = 'talents_candidate_bridge_settings';
const TALENTS_CANDIDATE_BRIDGE_NONCE_ACTION = 'talents_candidate_bridge_submit';
const TALENTS_CANDIDATE_BRIDGE_ADMIN_NONCE_ACTION = 'talents_candidate_bridge_test';
const TALENTS_CANDIDATE_BRIDGE_MAX_CV_BYTES = 5242880;
const TALENTS_CANDIDATE_BRIDGE_DEFAULT_API_URL = 'https://api.talentsag.ma/api/portal/applications';
const TALENTS_CANDIDATE_BRIDGE_CACHE_TTL = 300;
const TALENTS_CANDIDATE_BRIDGE_DETAIL_SLUG = 'detail-offre';
const TALENTS_CANDIDATE_BRIDGE_APPLY_SLUG = 'postuler-offre';

add_action('admin_menu', 'talents_candidate_bridge_register_settings_page');
add_action('admin_init', 'talents_candidate_bridge_register_settings');
add_action('admin_enqueue_scripts', 'talents_candidate_bridge_enqueue_admin_assets');
add_action('wp_enqueue_scripts', 'talents_candidate_bridge_enqueue_public_assets');
add_action('wp_ajax_talents_candidate_submit', 'talents_candidate_bridge_handle_submit');
add_action('wp_ajax_nopriv_talents_candidate_submit', 'talents_candidate_bridge_handle_submit');
add_action('wp_ajax_talents_candidate_bridge_test', 'talents_candidate_bridge_handle_connection_test');
add_shortcode('talents_candidature_form', 'talents_candidate_bridge_render_spontaneous_form');
add_shortcode('talents_jobs_list', 'talents_candidate_bridge_render_jobs_list');
add_shortcode('talents_job_detail', 'talents_candidate_bridge_render_job_detail');
add_shortcode('talents_job_apply', 'talents_candidate_bridge_render_job_apply');

function talents_candidate_bridge_defaults(): array
{
    return array(
        'api_url' => TALENTS_CANDIDATE_BRIDGE_DEFAULT_API_URL,
        'api_key' => '',
    );
}

function talents_candidate_bridge_get_settings(): array
{
    $saved = get_option(TALENTS_CANDIDATE_BRIDGE_OPTION, array());
    return wp_parse_args(is_array($saved) ? $saved : array(), talents_candidate_bridge_defaults());
}

function talents_candidate_bridge_register_settings(): void
{
    register_setting(
        'talents_candidate_bridge',
        TALENTS_CANDIDATE_BRIDGE_OPTION,
        array(
            'type' => 'array',
            'sanitize_callback' => 'talents_candidate_bridge_sanitize_settings',
            'default' => talents_candidate_bridge_defaults(),
        )
    );
}

function talents_candidate_bridge_sanitize_settings($input): array
{
    $previous = talents_candidate_bridge_get_settings();
    $input = is_array($input) ? $input : array();
    $api_url = isset($input['api_url']) ? esc_url_raw(trim(wp_unslash($input['api_url']))) : '';
    $api_key = isset($input['api_key']) ? trim((string) wp_unslash($input['api_key'])) : '';

    return array(
        'api_url' => $api_url !== '' ? $api_url : TALENTS_CANDIDATE_BRIDGE_DEFAULT_API_URL,
        'api_key' => $api_key !== '' ? sanitize_text_field($api_key) : (string) $previous['api_key'],
    );
}

function talents_candidate_bridge_register_settings_page(): void
{
    add_options_page(
        'Talents Candidate Bridge',
        'Talents Candidate Bridge',
        'manage_options',
        'talents-candidate-bridge',
        'talents_candidate_bridge_render_settings_page'
    );
}

function talents_candidate_bridge_enqueue_admin_assets(string $hook): void
{
    if ($hook !== 'settings_page_talents-candidate-bridge') {
        return;
    }

    wp_register_script('talents-candidate-bridge-admin', '', array(), TALENTS_CANDIDATE_BRIDGE_VERSION, true);
    wp_enqueue_script('talents-candidate-bridge-admin');
    wp_localize_script(
        'talents-candidate-bridge-admin',
        'TalentsCandidateBridgeAdmin',
        array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce(TALENTS_CANDIDATE_BRIDGE_ADMIN_NONCE_ACTION),
        )
    );
    wp_add_inline_script(
        'talents-candidate-bridge-admin',
        "document.addEventListener('DOMContentLoaded',function(){var b=document.querySelector('[data-talents-test-connection]');var r=document.querySelector('[data-talents-test-result]');if(!b||!r){return;}b.addEventListener('click',function(){b.disabled=true;r.textContent='Test en cours...';var f=new FormData();f.append('action','talents_candidate_bridge_test');f.append('nonce',TalentsCandidateBridgeAdmin.nonce);fetch(TalentsCandidateBridgeAdmin.ajaxUrl,{method:'POST',credentials:'same-origin',body:f}).then(function(x){return x.json();}).then(function(p){r.textContent=p&&p.data&&p.data.message?p.data.message:'Réponse indisponible.';r.style.color=p&&p.success?'#047857':'#b91c1c';}).catch(function(){r.textContent='Le test de connexion a échoué.';r.style.color='#b91c1c';}).finally(function(){b.disabled=false;});});});"
    );
}

function talents_candidate_bridge_render_settings_page(): void
{
    if (!current_user_can('manage_options')) {
        return;
    }

    $settings = talents_candidate_bridge_get_settings();
    ?>
    <div class="wrap">
        <h1>Talents Candidate Bridge</h1>
        <p>Configurez l'envoi sécurisé des candidatures vers l'API Talents Associate.</p>
        <form method="post" action="options.php">
            <?php settings_fields('talents_candidate_bridge'); ?>
            <table class="form-table" role="presentation">
                <tr>
                    <th scope="row"><label for="talents-api-url">URL API</label></th>
                    <td>
                        <input id="talents-api-url" name="<?php echo esc_attr(TALENTS_CANDIDATE_BRIDGE_OPTION); ?>[api_url]" type="url" class="regular-text" value="<?php echo esc_attr((string) $settings['api_url']); ?>" required>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="talents-api-key">Clé API WordPress</label></th>
                    <td>
                        <input id="talents-api-key" name="<?php echo esc_attr(TALENTS_CANDIDATE_BRIDGE_OPTION); ?>[api_key]" type="password" class="regular-text" value="" placeholder="<?php echo !empty($settings['api_key']) ? esc_attr('Clé enregistrée') : esc_attr('À renseigner'); ?>" autocomplete="new-password">
                        <p class="description">Laissez vide pour conserver la clé actuelle.</p>
                    </td>
                </tr>
            </table>
            <?php submit_button('Enregistrer les réglages'); ?>
        </form>
        <hr>
        <h2>Test de connexion</h2>
        <p>Ce test vérifie l'accessibilité de l'API des offres sans envoyer de candidature et sans afficher la clé.</p>
        <button type="button" class="button button-secondary" data-talents-test-connection>Tester la connexion</button>
        <p data-talents-test-result aria-live="polite"></p>
    </div>
    <?php
}

function talents_candidate_bridge_enqueue_public_assets(): void
{
    wp_enqueue_style(
        'talents-candidate-bridge',
        plugins_url('assets/talents-candidate-bridge.css', __FILE__),
        array(),
        TALENTS_CANDIDATE_BRIDGE_VERSION
    );
    wp_enqueue_script(
        'talents-candidate-bridge',
        plugins_url('assets/talents-candidate-bridge.js', __FILE__),
        array(),
        TALENTS_CANDIDATE_BRIDGE_VERSION,
        true
    );
    wp_localize_script(
        'talents-candidate-bridge',
        'TalentsCandidateBridge',
        array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce(TALENTS_CANDIDATE_BRIDGE_NONCE_ACTION),
            'action' => 'talents_candidate_submit',
            'loadingText' => 'Envoi en cours...',
            'successText' => 'Votre candidature a bien été reçue.',
            'genericError' => "Votre candidature n'a pas pu être envoyée. Veuillez réessayer.",
            'missingCv' => 'Veuillez ajouter votre CV au format PDF, DOC ou DOCX.',
        )
    );
}

function talents_candidate_bridge_render_spontaneous_form(): string
{
    $offers_result = talents_candidate_bridge_get_open_jobs();
    $offers = $offers_result['jobs'];
    $offers_error = $offers_result['error'];
    $submit_disabled = empty($offers);

    ob_start();
    ?>
    <form class="talents-candidate-form" data-talents-candidate-form method="post" enctype="multipart/form-data" novalidate>
        <div class="talents-candidate-form__grid">
            <label>
                <span>Opportunité *</span>
                <select name="opportunite" required <?php disabled($submit_disabled); ?>>
                    <option value="">Sélectionnez une offre</option>
                    <?php foreach ($offers as $offer) : ?>
                        <option value="<?php echo esc_attr($offer['id']); ?>"><?php echo esc_html(talents_candidate_bridge_offer_label($offer)); ?></option>
                    <?php endforeach; ?>
                </select>
                <?php if ($submit_disabled) : ?>
                    <small><?php echo esc_html($offers_error ?: 'Aucune offre n\'est disponible actuellement.'); ?></small>
                <?php endif; ?>
            </label>
            <?php echo talents_candidate_bridge_render_candidate_fields(); ?>
        </div>
        <?php echo talents_candidate_bridge_render_form_footer($submit_disabled); ?>
    </form>
    <?php
    return (string) ob_get_clean();
}

function talents_candidate_bridge_render_jobs_list(): string
{
    $result = talents_candidate_bridge_get_open_jobs();
    $jobs = $result['jobs'];
    $error = $result['error'];
    $keyword = talents_candidate_bridge_query_text('talents_keyword');
    $location = talents_candidate_bridge_query_text('talents_location');
    $contract = talents_candidate_bridge_query_text('talents_contract');
    $experience = talents_candidate_bridge_query_text('talents_experience');
    $filtered_jobs = talents_candidate_bridge_filter_jobs($jobs, $keyword, $location, $contract, $experience);
    $detail_page_available = talents_candidate_bridge_public_page_url(TALENTS_CANDIDATE_BRIDGE_DETAIL_SLUG) !== '';
    $apply_page_available = talents_candidate_bridge_public_page_url(TALENTS_CANDIDATE_BRIDGE_APPLY_SLUG) !== '';
    $locations = talents_candidate_bridge_unique_values($jobs, 'location');
    $contracts = talents_candidate_bridge_unique_values($jobs, 'contract_type');
    $experiences = talents_candidate_bridge_unique_values($jobs, 'experience_level');

    ob_start();
    ?>
    <section class="talents-jobs">
        <div class="talents-jobs__hero">
            <div>
                <span class="talents-jobs__eyebrow">Opportunités de carrières</span>
                <h1>Opportunités en cours</h1>
                <p>Découvrez les opportunités ouvertes et postulez directement avec votre CV.</p>
            </div>
            <div class="talents-jobs__count"><?php echo esc_html((string) count($jobs)); ?> offre(s) disponible(s)</div>
        </div>

        <form class="talents-jobs__filters" method="get">
            <label>
                <span>Recherche par mot-clé</span>
                <input type="search" name="talents_keyword" value="<?php echo esc_attr($keyword); ?>" placeholder="Poste, compétence, entreprise...">
            </label>
            <label>
                <span>Localisation</span>
                <select name="talents_location">
                    <option value="">Toutes les villes</option>
                    <?php foreach ($locations as $item) : ?>
                        <option value="<?php echo esc_attr($item); ?>" <?php selected($location, $item); ?>><?php echo esc_html($item); ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>
                <span>Type de contrat</span>
                <select name="talents_contract">
                    <option value="">Tous les contrats</option>
                    <?php foreach ($contracts as $item) : ?>
                        <option value="<?php echo esc_attr($item); ?>" <?php selected($contract, $item); ?>><?php echo esc_html($item); ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>
                <span>Niveau d'expérience</span>
                <select name="talents_experience">
                    <option value="">Tous les niveaux</option>
                    <?php foreach ($experiences as $item) : ?>
                        <option value="<?php echo esc_attr($item); ?>" <?php selected($experience, $item); ?>><?php echo esc_html($item); ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <button type="submit">Rechercher</button>
        </form>

        <?php if (empty($jobs)) : ?>
            <div class="talents-jobs__empty"><?php echo esc_html($error ?: 'Aucune offre n\'est disponible actuellement.'); ?></div>
        <?php elseif (empty($filtered_jobs)) : ?>
            <div class="talents-jobs__empty">Aucune offre ne correspond à vos critères.</div>
        <?php else : ?>
            <?php echo talents_candidate_bridge_page_warning($detail_page_available, 'La page WordPress "Détail de l\'offre" avec le slug detail-offre est introuvable ou non publiée.'); ?>
            <?php echo talents_candidate_bridge_page_warning($apply_page_available, 'La page WordPress "Postuler à l\'offre" avec le slug postuler-offre est introuvable ou non publiée.'); ?>
            <div class="talents-jobs__grid">
                <?php foreach ($filtered_jobs as $job) : ?>
                    <article class="talents-job-card">
                        <div class="talents-job-card__top">
                            <div>
                                <p class="talents-job-card__company"><?php echo esc_html($job['company'] ?: 'Talents Associate'); ?></p>
                                <h2><?php echo esc_html($job['title']); ?></h2>
                            </div>
                            <span class="talents-job-card__mark">TA</span>
                        </div>
                        <div class="talents-job-card__meta">
                            <?php echo talents_candidate_bridge_meta_badge($job['contract_type']); ?>
                            <?php echo talents_candidate_bridge_meta_badge($job['location']); ?>
                            <?php echo talents_candidate_bridge_meta_badge($job['experience_level']); ?>
                        </div>
                        <p class="talents-job-card__description"><?php echo esc_html(talents_candidate_bridge_excerpt($job['description'])); ?></p>
                        <?php echo talents_candidate_bridge_render_skills($job['required_skills']); ?>
                        <div class="talents-job-card__actions">
                            <?php echo talents_candidate_bridge_render_job_action('Voir détails', TALENTS_CANDIDATE_BRIDGE_DETAIL_SLUG, $job['id'], 'talents-button talents-button--outline'); ?>
                            <?php echo talents_candidate_bridge_render_job_action('Postuler', TALENTS_CANDIDATE_BRIDGE_APPLY_SLUG, $job['id'], 'talents-button'); ?>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </section>
    <?php
    return (string) ob_get_clean();
}

function talents_candidate_bridge_render_job_detail(): string
{
    $job = talents_candidate_bridge_current_job_from_query();
    if ($job === null) {
        return '<div class="talents-jobs__empty">Cette offre n\'est plus disponible.</div>';
    }
    $apply_page_available = talents_candidate_bridge_public_page_url(TALENTS_CANDIDATE_BRIDGE_APPLY_SLUG) !== '';

    ob_start();
    ?>
    <section class="talents-job-detail">
        <div class="talents-job-detail__header">
            <span class="talents-jobs__eyebrow">Détail de l'offre</span>
            <h1><?php echo esc_html($job['title']); ?></h1>
            <p><?php echo esc_html($job['company'] ?: 'Talents Associate'); ?></p>
            <?php echo talents_candidate_bridge_render_job_action('Postuler', TALENTS_CANDIDATE_BRIDGE_APPLY_SLUG, $job['id'], 'talents-button'); ?>
        </div>
        <?php echo talents_candidate_bridge_page_warning($apply_page_available, 'La page WordPress "Postuler à l\'offre" avec le slug postuler-offre est introuvable ou non publiée.'); ?>
        <div class="talents-job-detail__summary">
            <?php echo talents_candidate_bridge_detail_item('Client', $job['company']); ?>
            <?php echo talents_candidate_bridge_detail_item('Localisation', $job['location']); ?>
            <?php echo talents_candidate_bridge_detail_item('Contrat', $job['contract_type']); ?>
            <?php echo talents_candidate_bridge_detail_item('Expérience', $job['experience_level']); ?>
            <?php echo talents_candidate_bridge_detail_item('Niveau d\'études', $job['education_level']); ?>
            <?php echo talents_candidate_bridge_detail_item('Statut', $job['status']); ?>
        </div>
        <div class="talents-job-detail__body">
            <h2>Description complète</h2>
            <?php echo talents_candidate_bridge_render_formatted_text($job['description'] ?: 'Description non renseignée.'); ?>
            <h2>Compétences requises</h2>
            <?php echo talents_candidate_bridge_render_skills($job['required_skills'], true); ?>
            <?php if (!empty($job['preferred_skills'])) : ?>
                <h2>Compétences souhaitées</h2>
                <?php echo talents_candidate_bridge_render_skills($job['preferred_skills']); ?>
            <?php endif; ?>
        </div>
    </section>
    <?php
    return (string) ob_get_clean();
}

function talents_candidate_bridge_render_job_apply(): string
{
    $job = talents_candidate_bridge_current_job_from_query();
    if ($job === null) {
        return '<div class="talents-jobs__empty">Cette offre n\'est plus disponible.</div>';
    }

    ob_start();
    ?>
    <section class="talents-apply">
        <div class="talents-apply__selected">
            <span class="talents-jobs__eyebrow">Postuler à l'offre</span>
            <h1><?php echo esc_html($job['title']); ?></h1>
            <p><?php echo esc_html(talents_candidate_bridge_offer_label($job)); ?></p>
        </div>
        <form class="talents-candidate-form" data-talents-candidate-form method="post" enctype="multipart/form-data" novalidate>
            <div class="talents-candidate-form__grid">
                <input type="hidden" name="opportunite" value="<?php echo esc_attr($job['id']); ?>">
                <label>
                    <span>Prénom *</span>
                    <input type="text" name="prenom" required autocomplete="given-name">
                </label>
                <label>
                    <span>Nom *</span>
                    <input type="text" name="nom" required autocomplete="family-name">
                </label>
                <label>
                    <span>Email *</span>
                    <input type="email" name="email" required autocomplete="email">
                </label>
                <label>
                    <span>Téléphone</span>
                    <input type="tel" name="telephone" autocomplete="tel">
                </label>
                <label>
                    <span>Ville *</span>
                    <input type="text" name="ville" required autocomplete="address-level2">
                </label>
                <label class="talents-candidate-form__full">
                    <span>Message</span>
                    <textarea name="message" rows="5"></textarea>
                </label>
                <label class="talents-candidate-form__full talents-candidate-form__upload">
                    <span>CV obligatoire *</span>
                    <input type="file" name="cv" required accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
                    <small>Formats acceptés : PDF, DOC, DOCX. Taille maximale : 5 Mo.</small>
                </label>
            </div>
            <?php echo talents_candidate_bridge_render_form_footer(false); ?>
        </form>
    </section>
    <?php
    return (string) ob_get_clean();
}

function talents_candidate_bridge_render_candidate_fields(): string
{
    ob_start();
    ?>
    <label>
        <span>Nom *</span>
        <input type="text" name="nom" required autocomplete="family-name">
    </label>
    <label>
        <span>Prénom *</span>
        <input type="text" name="prenom" required autocomplete="given-name">
    </label>
    <label>
        <span>Email *</span>
        <input type="email" name="email" required autocomplete="email">
    </label>
    <label>
        <span>Téléphone</span>
        <input type="tel" name="telephone" autocomplete="tel">
    </label>
    <label>
        <span>Ville *</span>
        <input type="text" name="ville" required autocomplete="address-level2">
    </label>
    <label class="talents-candidate-form__full">
        <span>Message</span>
        <textarea name="message" rows="5"></textarea>
    </label>
    <label class="talents-candidate-form__full talents-candidate-form__upload">
        <span>CV obligatoire *</span>
        <input type="file" name="cv" required accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
        <small>Formats acceptés : PDF, DOC, DOCX. Taille maximale : 5 Mo.</small>
    </label>
    <?php
    return (string) ob_get_clean();
}

function talents_candidate_bridge_render_form_footer(bool $disabled): string
{
    ob_start();
    ?>
    <input type="hidden" name="action" value="talents_candidate_submit">
    <input type="hidden" name="talents_candidate_nonce" value="<?php echo esc_attr(wp_create_nonce(TALENTS_CANDIDATE_BRIDGE_NONCE_ACTION)); ?>">
    <button type="submit" class="talents-candidate-form__submit" <?php disabled($disabled); ?>>Envoyer ma candidature</button>
    <div class="talents-candidate-form__message" data-talents-candidate-message aria-live="polite"></div>
    <?php
    return (string) ob_get_clean();
}

function talents_candidate_bridge_handle_submit(): void
{
    $request_id = talents_candidate_bridge_request_id();

    if (!talents_candidate_bridge_verify_nonce()) {
        talents_candidate_bridge_log('nonce_invalid', $request_id, 403);
        wp_send_json_error(array('message' => 'Session expirée. Veuillez actualiser la page puis réessayer.'), 403);
    }

    $settings = talents_candidate_bridge_get_settings();
    if (empty($settings['api_url']) || empty($settings['api_key'])) {
        talents_candidate_bridge_log('config_missing', $request_id, 500);
        wp_send_json_error(array('message' => 'Le service de candidature n\'est pas encore configuré.'), 500);
    }

    $validation = talents_candidate_bridge_validate_request();
    if (!$validation['valid']) {
        talents_candidate_bridge_log('validation_failed', $request_id, 400);
        wp_send_json_error(array('message' => $validation['message']), 400);
    }

    $fields = $validation['fields'];
    $file = $validation['file'];
    $lock_key = talents_candidate_bridge_lock_key($fields, $file);
    if (get_transient($lock_key)) {
        talents_candidate_bridge_log('duplicate_submission_blocked', $request_id, 429);
        wp_send_json_error(array('message' => 'Votre candidature est déjà en cours d\'envoi. Veuillez patienter.'), 429);
    }

    set_transient($lock_key, '1', 90);
    $api_response = talents_candidate_bridge_send_to_fastapi($settings, $fields, $file, $request_id);
    delete_transient($lock_key);

    if ($api_response['success']) {
        wp_send_json_success(array('message' => 'Votre candidature a bien été reçue.'));
    }

    wp_send_json_error(
        array('message' => $api_response['message'] ?: 'Votre candidature contient une erreur. Veuillez vérifier les informations saisies.'),
        $api_response['status_code'] ?: 400
    );
}

function talents_candidate_bridge_handle_connection_test(): void
{
    if (!current_user_can('manage_options')) {
        wp_send_json_error(array('message' => 'Accès non autorisé.'), 403);
    }
    $nonce = isset($_POST['nonce']) ? sanitize_text_field(wp_unslash($_POST['nonce'])) : '';
    if ($nonce === '' || wp_verify_nonce($nonce, TALENTS_CANDIDATE_BRIDGE_ADMIN_NONCE_ACTION) === false) {
        wp_send_json_error(array('message' => 'Session expirée. Veuillez réessayer.'), 403);
    }

    $jobs_url = talents_candidate_bridge_jobs_url();
    $request_id = talents_candidate_bridge_request_id();
    $response = wp_remote_get($jobs_url, array('timeout' => 20));
    if (is_wp_error($response)) {
        talents_candidate_bridge_log('connection_test_failed', $request_id, 0);
        wp_send_json_error(array('message' => 'L\'API est inaccessible pour le moment.'), 503);
    }

    $status_code = (int) wp_remote_retrieve_response_code($response);
    talents_candidate_bridge_log('connection_test', $request_id, $status_code);
    if ($status_code >= 200 && $status_code < 300) {
        wp_send_json_success(array('message' => 'Connexion API réussie.'));
    }

    wp_send_json_error(array('message' => 'L\'API a répondu avec un statut inattendu.'), 502);
}

function talents_candidate_bridge_verify_nonce(): bool
{
    $nonce = isset($_POST['talents_candidate_nonce']) ? sanitize_text_field(wp_unslash($_POST['talents_candidate_nonce'])) : '';
    return $nonce !== '' && wp_verify_nonce($nonce, TALENTS_CANDIDATE_BRIDGE_NONCE_ACTION) !== false;
}

function talents_candidate_bridge_validate_request(): array
{
    $fields = array(
        'opportunite' => talents_candidate_bridge_post_text('opportunite'),
        'nom' => talents_candidate_bridge_post_text('nom'),
        'prenom' => talents_candidate_bridge_post_text('prenom'),
        'email' => sanitize_email(talents_candidate_bridge_post_text('email')),
        'telephone' => talents_candidate_bridge_post_text('telephone'),
        'ville' => talents_candidate_bridge_post_text('ville'),
        'message' => talents_candidate_bridge_post_textarea('message'),
    );

    foreach (array('opportunite', 'nom', 'prenom', 'email', 'ville') as $field_name) {
        if ($fields[$field_name] === '') {
            return array('valid' => false, 'message' => 'Veuillez compléter tous les champs obligatoires.');
        }
    }

    if (!talents_candidate_bridge_is_uuid($fields['opportunite'])) {
        return array('valid' => false, 'message' => 'Veuillez sélectionner une offre disponible.');
    }

    if (talents_candidate_bridge_get_job_detail($fields['opportunite']) === null) {
        return array('valid' => false, 'message' => 'Cette offre n\'est plus disponible.');
    }

    if (!is_email($fields['email'])) {
        return array('valid' => false, 'message' => 'Veuillez saisir une adresse e-mail valide.');
    }

    if (!isset($_FILES['cv']) || !is_array($_FILES['cv'])) {
        return array('valid' => false, 'message' => 'Veuillez ajouter votre CV au format PDF, DOC ou DOCX.');
    }

    $file = $_FILES['cv'];
    if (!empty($file['error'])) {
        return array('valid' => false, 'message' => talents_candidate_bridge_upload_error_message((int) $file['error']));
    }

    if (empty($file['tmp_name']) || !is_uploaded_file($file['tmp_name'])) {
        return array('valid' => false, 'message' => 'Le fichier CV est introuvable. Veuillez réessayer.');
    }

    if ((int) $file['size'] <= 0) {
        return array('valid' => false, 'message' => 'Le fichier CV est vide.');
    }

    if ((int) $file['size'] > TALENTS_CANDIDATE_BRIDGE_MAX_CV_BYTES) {
        return array('valid' => false, 'message' => 'Le CV dépasse la taille maximale autorisée de 5 Mo.');
    }

    $filename = sanitize_file_name((string) $file['name']);
    $extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    $allowed_mimes = talents_candidate_bridge_allowed_mimes();
    $checked = wp_check_filetype_and_ext($file['tmp_name'], $filename, $allowed_mimes);

    if (!in_array($extension, array('pdf', 'doc', 'docx'), true) || empty($checked['ext'])) {
        return array('valid' => false, 'message' => 'Format de CV non autorisé. Importez un fichier PDF, DOC ou DOCX.');
    }

    if (function_exists('finfo_open')) {
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mime = $finfo ? finfo_file($finfo, $file['tmp_name']) : '';
        if ($finfo) {
            finfo_close($finfo);
        }
        $valid_mimes = array_values($allowed_mimes);
        if ($mime && !in_array($mime, $valid_mimes, true) && !($extension === 'docx' && $mime === 'application/zip')) {
            return array('valid' => false, 'message' => 'Le type réel du fichier CV n\'est pas autorisé.');
        }
    }

    $file['name'] = $filename;
    return array('valid' => true, 'fields' => $fields, 'file' => $file);
}

function talents_candidate_bridge_allowed_mimes(): array
{
    return array(
        'pdf' => 'application/pdf',
        'doc' => 'application/msword',
        'docx' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    );
}

function talents_candidate_bridge_get_open_jobs(): array
{
    $jobs_url = talents_candidate_bridge_jobs_url();
    $cache_key = 'talents_candidate_jobs_' . md5($jobs_url);
    $cached = get_transient($cache_key);
    if (is_array($cached)) {
        return $cached;
    }

    $request_id = talents_candidate_bridge_request_id();
    $response = wp_remote_get($jobs_url, array('timeout' => 20));
    if (is_wp_error($response)) {
        talents_candidate_bridge_log('jobs_fetch_failed', $request_id, 0);
        $result = array('jobs' => array(), 'error' => 'Le service des offres est momentanément indisponible.');
        set_transient($cache_key, $result, 60);
        return $result;
    }

    $status_code = (int) wp_remote_retrieve_response_code($response);
    talents_candidate_bridge_log('jobs_fetch', $request_id, $status_code);
    if ($status_code < 200 || $status_code >= 300) {
        $result = array('jobs' => array(), 'error' => 'Le service des offres est momentanément indisponible.');
        set_transient($cache_key, $result, 60);
        return $result;
    }

    $decoded = json_decode((string) wp_remote_retrieve_body($response), true);
    if (!is_array($decoded)) {
        $result = array('jobs' => array(), 'error' => 'Le service des offres est momentanément indisponible.');
        set_transient($cache_key, $result, 60);
        return $result;
    }

    $jobs = array_values(array_filter(array_map('talents_candidate_bridge_normalize_offer', $decoded)));
    $result = array(
        'jobs' => $jobs,
        'error' => empty($jobs) ? 'Aucune offre n\'est disponible actuellement.' : '',
    );
    set_transient($cache_key, $result, TALENTS_CANDIDATE_BRIDGE_CACHE_TTL);
    return $result;
}

function talents_candidate_bridge_get_job_detail(string $job_id): ?array
{
    if (!talents_candidate_bridge_is_uuid($job_id)) {
        return null;
    }

    $cache_key = 'talents_candidate_job_' . md5($job_id);
    $cached = get_transient($cache_key);
    if (is_array($cached)) {
        return $cached;
    }

    $request_id = talents_candidate_bridge_request_id();
    $response = wp_remote_get(talents_candidate_bridge_job_detail_api_url($job_id), array('timeout' => 20));
    if (is_wp_error($response)) {
        talents_candidate_bridge_log('job_detail_failed', $request_id, 0);
        return null;
    }

    $status_code = (int) wp_remote_retrieve_response_code($response);
    talents_candidate_bridge_log('job_detail', $request_id, $status_code);
    if ($status_code < 200 || $status_code >= 300) {
        return null;
    }

    $decoded = json_decode((string) wp_remote_retrieve_body($response), true);
    $job = talents_candidate_bridge_normalize_offer($decoded);
    if ($job === null) {
        return null;
    }

    set_transient($cache_key, $job, TALENTS_CANDIDATE_BRIDGE_CACHE_TTL);
    return $job;
}

function talents_candidate_bridge_current_job_from_query(): ?array
{
    $job_id = isset($_GET['job_id']) ? sanitize_text_field(wp_unslash($_GET['job_id'])) : '';
    if (!talents_candidate_bridge_is_uuid($job_id)) {
        return null;
    }
    return talents_candidate_bridge_get_job_detail($job_id);
}

function talents_candidate_bridge_normalize_offer($offer): ?array
{
    if (!is_array($offer)) {
        return null;
    }

    $id = isset($offer['id']) ? sanitize_text_field((string) $offer['id']) : '';
    $title = isset($offer['title']) ? sanitize_text_field((string) $offer['title']) : '';
    if ($id === '' || $title === '' || !talents_candidate_bridge_is_uuid($id)) {
        return null;
    }

    return array(
        'id' => $id,
        'title' => $title,
        'company' => talents_candidate_bridge_offer_optional_text($offer, array('company_name', 'company', 'client', 'client_name', 'entreprise')),
        'location' => talents_candidate_bridge_offer_optional_text($offer, array('location', 'city', 'ville', 'localisation')),
        'contract_type' => talents_candidate_bridge_offer_optional_text($offer, array('contract_type', 'contract', 'type_contrat')),
        'experience_level' => talents_candidate_bridge_offer_optional_text($offer, array('experience_level', 'experience', 'niveau_experience')),
        'education_level' => talents_candidate_bridge_offer_optional_text($offer, array('education_level', 'study_level', 'niveau_etudes')),
        'status' => talents_candidate_bridge_offer_optional_text($offer, array('status', 'statut')),
        'description' => talents_candidate_bridge_offer_optional_text($offer, array('description', 'mission', 'details')),
        'required_skills' => talents_candidate_bridge_offer_list($offer, array('required_skills', 'technical_skills', 'competences_techniques')),
        'preferred_skills' => talents_candidate_bridge_offer_list($offer, array('soft_skills', 'preferred_skills', 'behavioral_skills', 'desired_skills', 'competences_souhaitees', 'competences_comportementales')),
    );
}

function talents_candidate_bridge_offer_optional_text(array $offer, array $keys): string
{
    foreach ($keys as $key) {
        if (!empty($offer[$key]) && is_scalar($offer[$key])) {
            return sanitize_text_field((string) $offer[$key]);
        }
    }
    return '';
}

function talents_candidate_bridge_offer_list(array $offer, array $keys): array
{
    foreach ($keys as $key) {
        if (empty($offer[$key])) {
            continue;
        }
        if (is_array($offer[$key])) {
            $items = array();
            foreach ($offer[$key] as $entry) {
                foreach (preg_split('/[;\n]+/', (string) $entry) as $item) {
                    $clean = sanitize_text_field(trim($item));
                    if ($clean !== '') {
                        $items[] = $clean;
                    }
                }
            }
            return array_values(array_unique($items));
        }
        if (is_string($offer[$key])) {
            return array_values(array_filter(array_map('trim', preg_split('/[;\n]+/', sanitize_text_field($offer[$key])))));
        }
    }
    return array();
}

function talents_candidate_bridge_offer_label(array $offer): string
{
    $parts = array($offer['title']);
    if (!empty($offer['company'])) {
        $parts[] = $offer['company'];
    }
    if (!empty($offer['location'])) {
        $parts[] = $offer['location'];
    }
    return implode(' — ', $parts);
}

function talents_candidate_bridge_filter_jobs(array $jobs, string $keyword, string $location, string $contract, string $experience): array
{
    return array_values(array_filter($jobs, function (array $job) use ($keyword, $location, $contract, $experience): bool {
        if ($location !== '' && $job['location'] !== $location) {
            return false;
        }
        if ($contract !== '' && $job['contract_type'] !== $contract) {
            return false;
        }
        if ($experience !== '' && $job['experience_level'] !== $experience) {
            return false;
        }
        if ($keyword === '') {
            return true;
        }
        $haystack = strtolower(implode(' ', array_merge(array(
            $job['title'],
            $job['company'],
            $job['location'],
            $job['description'],
        ), $job['required_skills'], $job['preferred_skills'])));
        return strpos($haystack, strtolower($keyword)) !== false;
    }));
}

function talents_candidate_bridge_unique_values(array $jobs, string $key): array
{
    $values = array();
    foreach ($jobs as $job) {
        if (!empty($job[$key])) {
            $values[] = $job[$key];
        }
    }
    $values = array_values(array_unique($values));
    sort($values);
    return $values;
}

function talents_candidate_bridge_jobs_url(): string
{
    $settings = talents_candidate_bridge_get_settings();
    return talents_candidate_bridge_api_base_url((string) $settings['api_url']) . '/api/portal/jobs';
}

function talents_candidate_bridge_job_detail_api_url(string $job_id): string
{
    $settings = talents_candidate_bridge_get_settings();
    return talents_candidate_bridge_api_base_url((string) $settings['api_url']) . '/api/portal/jobs/' . rawurlencode($job_id);
}

function talents_candidate_bridge_api_base_url(string $api_url): string
{
    $parts = wp_parse_url(trim($api_url));
    if (empty($parts['scheme']) || empty($parts['host'])) {
        return 'https://api.talentsag.ma';
    }
    return $parts['scheme'] . '://' . $parts['host'];
}

function talents_candidate_bridge_public_page_url(string $slug): string
{
    $page = get_page_by_path($slug, OBJECT, 'page');
    if (!$page || $page->post_status !== 'publish') {
        return '';
    }
    return (string) get_permalink($page->ID);
}

function talents_candidate_bridge_job_url(string $slug, string $job_id): string
{
    $base_url = talents_candidate_bridge_public_page_url($slug);
    if ($base_url === '') {
        return '';
    }
    return add_query_arg('job_id', rawurlencode($job_id), $base_url);
}

function talents_candidate_bridge_render_job_action(string $label, string $slug, string $job_id, string $class): string
{
    $url = talents_candidate_bridge_job_url($slug, $job_id);
    if ($url === '') {
        return '<span class="' . esc_attr($class) . ' talents-button--disabled" aria-disabled="true">' . esc_html($label) . '</span>';
    }
    return '<a class="' . esc_attr($class) . '" href="' . esc_url($url) . '">' . esc_html($label) . '</a>';
}

function talents_candidate_bridge_page_warning(bool $page_available, string $message): string
{
    if ($page_available || !current_user_can('manage_options')) {
        return '';
    }
    return '<div class="talents-jobs__admin-warning">' . esc_html($message) . '</div>';
}

function talents_candidate_bridge_query_text(string $key): string
{
    return isset($_GET[$key]) ? sanitize_text_field(wp_unslash($_GET[$key])) : '';
}

function talents_candidate_bridge_is_uuid(string $value): bool
{
    return (bool) preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i', $value);
}

function talents_candidate_bridge_excerpt(string $text): string
{
    if ($text === '') {
        return 'Description non renseignée.';
    }
    return function_exists('wp_trim_words') ? wp_trim_words($text, 28, '...') : mb_substr($text, 0, 180);
}

function talents_candidate_bridge_meta_badge(string $value): string
{
    if ($value === '') {
        return '';
    }
    return '<span>' . esc_html($value) . '</span>';
}

function talents_candidate_bridge_render_skills(array $skills, bool $empty_message = false): string
{
    if (empty($skills)) {
        return $empty_message ? '<p class="talents-job-detail__empty">Non renseigné.</p>' : '';
    }
    $html = '<div class="talents-job-card__skills">';
    foreach (array_slice($skills, 0, 8) as $skill) {
        $html .= '<span>' . esc_html($skill) . '</span>';
    }
    $html .= '</div>';
    return $html;
}

function talents_candidate_bridge_render_formatted_text(string $text): string
{
    $normalized = trim(str_replace(array("\r\n", "\r"), "\n", $text));
    if ($normalized === '') {
        return '<ul class="talents-job-detail__list"><li>Description non renseignée.</li></ul>';
    }

    $lines = array_values(array_filter(array_map('trim', explode("\n", $normalized)), static function (string $line): bool {
        return $line !== '';
    }));
    $items = array();
    foreach ($lines as $line) {
        $clean_line = trim((string) preg_replace('/^([-*•]|\d+[.)])\s+/', '', $line));
        $parts = preg_split('/(?<=[.!?])\s+(?=[A-ZÀ-Ö])/u', $clean_line);
        foreach ($parts ?: array($clean_line) as $part) {
            $item = trim((string) $part);
            if ($item !== '') {
                $items[] = $item;
            }
        }
    }

    if (empty($items)) {
        $items[] = 'Description non renseignée.';
    }

    $html = '<ul class="talents-job-detail__list">';
    foreach ($items as $item) {
        $html .= '<li>' . esc_html($item) . '</li>';
    }
    $html .= '</ul>';
    return $html;
}

function talents_candidate_bridge_detail_item(string $label, string $value): string
{
    return '<div><span>' . esc_html($label) . '</span><strong>' . esc_html($value !== '' ? $value : 'Non renseigné') . '</strong></div>';
}

function talents_candidate_bridge_send_to_fastapi(array $settings, array $fields, array $file, string $request_id): array
{
    if (function_exists('curl_init')) {
        return talents_candidate_bridge_send_with_curl($settings, $fields, $file, $request_id);
    }
    return talents_candidate_bridge_send_with_wp_http($settings, $fields, $file, $request_id);
}

function talents_candidate_bridge_send_with_curl(array $settings, array $fields, array $file, string $request_id): array
{
    $curl = curl_init((string) $settings['api_url']);
    $payload = $fields;
    $payload['cv'] = new CURLFile($file['tmp_name'], (string) $file['type'], (string) $file['name']);

    curl_setopt_array(
        $curl,
        array(
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_HTTPHEADER => array(
                'X-Talents-Api-Key: ' . (string) $settings['api_key'],
                'X-Talents-Request-Id: ' . $request_id,
            ),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 60,
        )
    );

    $body = curl_exec($curl);
    $status_code = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    curl_close($curl);

    if ($body === false) {
        talents_candidate_bridge_log('curl_error', $request_id, 0);
        return talents_candidate_bridge_api_result(false, 0, 'Le service de candidature est indisponible.');
    }
    return talents_candidate_bridge_parse_api_response((string) $body, $status_code, $request_id);
}

function talents_candidate_bridge_send_with_wp_http(array $settings, array $fields, array $file, string $request_id): array
{
    $boundary = 'talents-' . wp_generate_uuid4();
    $body = talents_candidate_bridge_build_multipart_body($fields, $file, $boundary);
    $response = wp_remote_post(
        (string) $settings['api_url'],
        array(
            'timeout' => 60,
            'headers' => array(
                'Content-Type' => 'multipart/form-data; boundary=' . $boundary,
                'X-Talents-Api-Key' => (string) $settings['api_key'],
                'X-Talents-Request-Id' => $request_id,
            ),
            'body' => $body,
        )
    );

    if (is_wp_error($response)) {
        talents_candidate_bridge_log('wp_http_error', $request_id, 0);
        return talents_candidate_bridge_api_result(false, 0, 'Le service de candidature est indisponible.');
    }

    return talents_candidate_bridge_parse_api_response(
        (string) wp_remote_retrieve_body($response),
        (int) wp_remote_retrieve_response_code($response),
        $request_id
    );
}

function talents_candidate_bridge_parse_api_response(string $body, int $status_code, string $request_id): array
{
    $decoded = json_decode($body, true);
    $success = $status_code === 201 && is_array($decoded) && !empty($decoded['success']);
    talents_candidate_bridge_log($success ? 'api_success' : 'api_error', $request_id, $status_code);
    if ($success) {
        return talents_candidate_bridge_api_result(true, $status_code, 'Votre candidature a bien été reçue.');
    }
    return talents_candidate_bridge_api_result(false, $status_code, talents_candidate_bridge_public_error_message($decoded, $status_code));
}

function talents_candidate_bridge_public_error_message($decoded, int $status_code): string
{
    if ($status_code === 0 || $status_code >= 500) {
        return 'Le service de candidature est momentanément indisponible.';
    }
    if ($status_code === 401 || $status_code === 403) {
        return 'Le service de candidature n\'est pas correctement configuré.';
    }
    if ($status_code === 400 || $status_code === 422) {
        if (is_array($decoded) && isset($decoded['detail']) && is_string($decoded['detail'])) {
            return sanitize_text_field($decoded['detail']);
        }
        return 'Veuillez vérifier les informations saisies et le format du CV.';
    }
    return 'Votre candidature n\'a pas pu être envoyée. Veuillez réessayer.';
}

function talents_candidate_bridge_build_multipart_body(array $fields, array $file, string $boundary): string
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

function talents_candidate_bridge_api_result(bool $success, int $status_code, string $message): array
{
    return array(
        'success' => $success,
        'status_code' => $status_code,
        'message' => $message,
    );
}

function talents_candidate_bridge_post_text(string $field): string
{
    return isset($_POST[$field]) ? sanitize_text_field(wp_unslash($_POST[$field])) : '';
}

function talents_candidate_bridge_post_textarea(string $field): string
{
    return isset($_POST[$field]) ? sanitize_textarea_field(wp_unslash($_POST[$field])) : '';
}

function talents_candidate_bridge_upload_error_message(int $error_code): string
{
    $messages = array(
        UPLOAD_ERR_INI_SIZE => 'Le fichier dépasse la taille autorisée par le serveur.',
        UPLOAD_ERR_FORM_SIZE => 'Le fichier dépasse la taille autorisée par le formulaire.',
        UPLOAD_ERR_PARTIAL => 'Le fichier CV n\'a été chargé que partiellement.',
        UPLOAD_ERR_NO_FILE => 'Veuillez ajouter votre CV.',
        UPLOAD_ERR_NO_TMP_DIR => 'Le serveur ne peut pas recevoir le fichier temporaire.',
        UPLOAD_ERR_CANT_WRITE => 'Le serveur ne peut pas enregistrer le fichier temporaire.',
        UPLOAD_ERR_EXTENSION => 'Le chargement du fichier a été bloqué par le serveur.',
    );
    return $messages[$error_code] ?? 'Le fichier CV n\'a pas pu être chargé.';
}

function talents_candidate_bridge_request_id(): string
{
    return function_exists('wp_generate_uuid4') ? wp_generate_uuid4() : bin2hex(random_bytes(16));
}

function talents_candidate_bridge_lock_key(array $fields, array $file): string
{
    $fingerprint = implode('|', array(
        strtolower((string) $fields['email']),
        strtolower((string) $fields['opportunite']),
        (string) $file['name'],
        (string) $file['size'],
    ));
    return 'talents_candidate_bridge_' . md5($fingerprint);
}

function talents_candidate_bridge_log(string $event, string $request_id, int $status_code): void
{
    error_log(sprintf('[talents-candidate-bridge] event=%s request_id=%s status=%d', $event, $request_id, $status_code));
}
