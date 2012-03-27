<?php
 $down = $_COOKIE["downloadrequested"];
 $lic = $_SERVER["QUERY_STRING"];
 $host = $_SERVER["HTTP_HOST"];
 $doc = $_SERVER["DOCUMENT_ROOT"];
 $eula = $_COOKIE["eula"];
 $fn = $doc.$down;
 if (file_exists($fn) and is_file($fn)) {
    $repl = dirname($down);
 } else {
    $repl = $down;
 }

 $handle = @fopen($doc."/licenses/".$lic.".html", "r");
 if ($handle) {
    while (($buffer = fgets($handle, 4096)) !== false) {
        $eula = str_replace("src=\"EULA.txt\"", "src=".$repl."/EULA.txt", $buffer);
        echo $eula;
    }
    if (!feof($handle)) {
        echo "Error: unexpected fgets() fail\n";
    }
    fclose($handle);
 }
?>
