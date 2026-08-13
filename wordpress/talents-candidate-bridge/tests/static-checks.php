<?php

$root = dirname(__DIR__);
$files = array(
    $root . '/talents-candidate-bridge.php',
    $root . '/assets/talents-candidate-bridge.js',
    $root . '/assets/talents-candidate-bridge.css',
    $root . '/README.md',
);

foreach ($files as $file) {
    if (!is_file($file)) {
        fwrite(STDERR, "Fichier manquant : {$file}\n");
        exit(1);
    }
}

$plugin = file_get_contents($root . '/talents-candidate-bridge.php');
$javascript = file_get_contents($root . '/assets/talents-candidate-bridge.js');
$stylesheet = file_get_contents($root . '/assets/talents-candidate-bridge.css');
$readme = file_get_contents($root . '/README.md');
$all = $plugin . "\n" . $javascript . "\n" . $stylesheet . "\n" . $readme;

$local_host = 'local' . 'host';
$loopback = '127.0.' . '0.1';
$secret_prefix = 's' . 'k-';
$wp_mail_function = 'wp_' . 'mail';
$duplicated_api_path = '/api' . '/api';
$fixed_detail_url = '/detail-' . 'offre/';
$fixed_apply_url = '/postuler-' . 'offre/';

$checks = array(
    'shortcode candidature existant conservé' => strpos($plugin, "add_shortcode('talents_candidature_form'") !== false,
    'shortcode liste offres ajouté' => strpos($plugin, "add_shortcode('talents_jobs_list'") !== false,
    'shortcode détail offre ajouté' => strpos($plugin, "add_shortcode('talents_job_detail'") !== false,
    'shortcode postuler offre ajouté' => strpos($plugin, "add_shortcode('talents_job_apply'") !== false,
    'URL candidature production présente' => strpos($plugin, 'https://api.talentsag.ma/api/portal/applications') !== false,
    'endpoint liste offres utilisé' => strpos($plugin, '/api/portal/jobs') !== false,
    'endpoint détail offre utilisé' => strpos($plugin, '/api/portal/jobs/') !== false,
    'offres chargées par wp_remote_get' => strpos($plugin, 'wp_remote_get($jobs_url') !== false,
    'détail chargé par wp_remote_get' => strpos($plugin, 'wp_remote_get(talents_candidate_bridge_job_detail_api_url') !== false,
    'cache offres 5 minutes' => strpos($plugin, 'TALENTS_CANDIDATE_BRIDGE_CACHE_TTL = 300') !== false,
    'paramètre job_id lu et validé' => strpos($plugin, "\$_GET['job_id']") !== false && strpos($plugin, 'talents_candidate_bridge_is_uuid($job_id)') !== false,
    'UUID exact envoyé dans opportunite' => strpos($plugin, 'name="opportunite" value="<?php echo esc_attr($job[\'id\']); ?>"') !== false,
    'aucun champ opportunité libre dans talents_job_apply' => strpos($plugin, 'function talents_candidate_bridge_render_job_apply') !== false && strpos($plugin, '<input type="hidden" name="opportunite"') !== false,
    'pages résolues par slug' => strpos($plugin, 'get_page_by_path($slug, OBJECT, \'page\')') !== false,
    'permalien WordPress utilisé' => strpos($plugin, 'get_permalink($page->ID)') !== false,
    'job_id ajouté par add_query_arg' => strpos($plugin, "add_query_arg('job_id'") !== false,
    'pas de lien fixe détail dans les boutons' => strpos($plugin, $fixed_detail_url) === false,
    'pas de lien fixe postuler dans les boutons' => strpos($plugin, $fixed_apply_url) === false,
    'soft skills utilisées comme compétences souhaitées' => strpos($plugin, "'soft_skills', 'preferred_skills'") !== false,
    'description publique formatée' => strpos($plugin, 'talents_candidate_bridge_render_formatted_text') !== false,
    'description rendue en liste HTML' => strpos($plugin, '<ul class="talents-job-detail__list">') !== false,
    'compétences souhaitées masquées si vides' => strpos($plugin, "if (!empty(\$job['preferred_skills']))") !== false,
    'header API présent côté serveur' => strpos($plugin, 'X-Talents-Api-Key') !== false,
    'clé absente du JavaScript' => strpos($javascript, 'X-Talents-Api-Key') === false && strpos($javascript, 'api_key') === false,
    'aucun envoi email WordPress' => strpos($plugin, $wp_mail_function) === false,
    'aucune URL locale' => strpos($all, $local_host) === false && strpos($all, $loopback) === false,
    'absence de chemin API dupliqué' => strpos($all, $duplicated_api_path) === false,
    'taille CV 5 Mo' => strpos($plugin, '5242880') !== false,
    'extensions CV attendues' => strpos($plugin, "'pdf'") !== false && strpos($plugin, "'doc'") !== false && strpos($plugin, "'docx'") !== false,
    'design responsive présent' => strpos($stylesheet, '@media (max-width: 720px)') !== false && strpos($stylesheet, 'grid-template-columns') !== false,
    'aucun placeholder de secret évident' => strpos($all, 'une-cle') === false && strpos($all, $secret_prefix) === false,
);

foreach ($checks as $label => $passed) {
    echo ($passed ? '[OK] ' : '[ERREUR] ') . $label . PHP_EOL;
    if (!$passed) {
        exit(1);
    }
}

echo 'Tests statiques terminés.' . PHP_EOL;
