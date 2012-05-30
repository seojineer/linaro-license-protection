<?php

require_once("LicenseHelper.php");
require_once("BuildInfo.php");

$down = $_COOKIE["downloadrequested"];
$host = $_SERVER["HTTP_HOST"];
$doc = $_SERVER["DOCUMENT_ROOT"];
$domain = $_SERVER["CO_DOMAIN"];
$fn = $doc.$down; // Filename on server
$flist = array();
$eula = '';
$bi_found = 0;

if (preg_match("/.*openid.*/", $fn) or preg_match("/.*restricted.*/", $fn) or preg_match("/.*private.*/", $fn)) {
    LicenseHelper::redirect_with_status($down, $domain, 200);
}

if (file_exists($fn) and LicenseHelper::checkFile($fn)) { // Requested download is file
    $search_dir = dirname($fn);
    $repl = dirname($down);
    $name_only = array(basename($down), '');
} elseif (is_dir($fn)) { // Requested download is directory
    $search_dir = $fn;
    $repl = $down;
    $name_only = array();
} else { // Requested download not found on server
    LicenseHelper::redirect_with_status($down, $domain, 404);
}

if (file_exists($search_dir."/BUILD-INFO.txt")) {
    $bi_found = 1;
    $bi = new BuildInfo($search_dir."/BUILD-INFO.txt");
    $theme = $bi->getTheme($name_only[0]);
    $lic_type = $bi->getLicenseType($name_only[0]);
    $lic_text = $bi->getLicenseText($name_only[0]);
} else {
    $flist = LicenseHelper::getFilesList($search_dir);
    if (!empty($name_only)) {
        $pattern = "/^".$name_only[0]."\.EULA\.txt.*/";
        $eula = LicenseHelper::findFileByPattern($flist, $pattern);
    }
}

if (LicenseHelper::checkFile($fn)) {
    if ($bi_found) {
        if ($lic_type == 'open')
            LicenseHelper::redirect_with_status($down, $domain, 200);
        elseif (($theme != false) or ($lic_text != false))
            $template_content = file_get_contents($doc."/licenses/".$theme.".html");
        else
            LicenseHelper::redirect_with_status($down, $domain, 403);
    } else {
        if (LicenseHelper::checkFile($doc."/".$repl."/".$eula)) {
            // Special EULA found
            $theme = LicenseHelper::getTheme($eula, $down);
        } elseif (LicenseHelper::checkFile($doc."/".$repl."/EULA.txt")) {
            // No special EULA found
            $theme = LicenseHelper::getTheme("EULA.txt", $down);
        } elseif (LicenseHelper::findFileByPattern($flist, "/.*EULA.txt.*/")) {
            // If file is requested but no special EULA for it and no EULA.txt
            // is present, look for any EULA and if found decide that current
            // file is not protected.
            LicenseHelper::redirect_with_status($down, $domain, 200);
        } else {
            LicenseHelper::redirect_with_status($down, $domain, 403);
        }
        $template_content = file_get_contents($doc."/licenses/".$theme.".html");
        $lic_text = file_get_contents($doc."/licenses/".$theme.".txt");
    }
} elseif (is_dir($fn)) {
    if (empty($flist)
        or LicenseHelper::findFileByPattern($flist, "/.*EULA.txt.*/")
        or $bi_found) {
            // Directory contains only subdirs or any EULA or BUILD-INFO.txt
            LicenseHelper::redirect_with_status($down, $domain, 200);
        } else {
            // No special EULA, no EULA.txt, no OPEN-EULA.txt found
            LicenseHelper::redirect_with_status($down, $domain, 403);
        }
} else {
    LicenseHelper::redirect_with_status($down, $domain, 403);
}

$out = str_replace("EULA.txt", $lic_text, $template_content);
echo $out;
?>
