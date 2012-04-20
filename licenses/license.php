<?php
 $down = $_COOKIE["downloadrequested"];
 $lic = $_SERVER["QUERY_STRING"];
 $host = $_SERVER["HTTP_HOST"];
 $doc = $_SERVER["DOCUMENT_ROOT"];
 $fn = $doc.$down;
 if (file_exists($fn) and is_file($fn)) {
    $repl = dirname($down);
 } else {
    $repl = $down;
 }

 $template_content = file_get_contents($doc."/licenses/".$lic.".html");
 $eula_content = file_get_contents($doc."/licenses/".$lic.".txt");

 $out = str_replace("EULA.txt", $eula_content, $template_content);
 echo $out;
?>
