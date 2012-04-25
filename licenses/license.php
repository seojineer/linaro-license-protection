<?php
// Get list of files into array to process them later.
// Used to find special licenses and dirs with only subdirs.
function getFilesList($dirname)
{
	$files = array(); 
	if ($handle = opendir($dirname)) {
		while ($handle && false !== ($entry = readdir($handle))) {
			if ($entry != "." && $entry != ".." && !is_dir($dirname.$entry) && !is_link($dirname.$entry)) {
				$files[] = $entry;
			}
		}
	}
	closedir($handle);
	return $files;
}

// Get array of file name and extension from full filename.
function splitFilename($filename)
{
	$pos = strpos($filename, '.');
	if ($pos === false) { // dot is not found in the filename
		return array($filename, ''); // no extension
	} else {
		$basename = substr($filename, 0, $pos);
		$extension = substr($filename, $pos+1);
		return array($basename, $extension);
	}
}

// Find special EULA based on filename template.
function findSpecialEULA($fl, $pattern)
{
	if (!empty($fl)) {
		foreach ($fl as $f) {
			if (preg_match($pattern, $f, $matches)) {
				return $f;
			}
		}
	}
       	return false;
}

// Get license theme name from EULA filename.
function getTheme($eula, $down)
{
	if ($eula != 'EULA.txt') { // Special EULA file was found
		$theme = array_pop(explode(".", $eula));
	} else { // No special EULA file was found
		$eula = "EULA.txt";
		if (preg_match("/.*snowball.*/", $down)) {
			$theme = "ste";
		} elseif (preg_match("/.*origen.*/", $down)) {
			$theme = "samsung";
		} else {
			$theme = "linaro";
		}
	}
	return $theme;
}

function status_forbidden($dir)
{
	header("Status: 403");
	header("HTTP/1.1 403 Forbidden");
	echo "<h1>Forbidden</h1>";
	echo "You don't have permission to access ".$dir." on this server.";
	exit;
}

function status_ok($dir, $domain)
{
	header("Status: 200");
	header("Location: ".$dir);
	setcookie("redirectlicensephp", "yes", 0, "/", ".".$domain);
	exit;
}

function status_not_found()
{
	header("Status: 404");
	header("HTTP/1.0 404 Not Found");
	echo "<h1>404 Not Found</h1>";
	echo "The requested URL was not found on this server.";
	exit;
}

$down = $_COOKIE["downloadrequested"];
$host = $_SERVER["HTTP_HOST"];
$doc = $_SERVER["DOCUMENT_ROOT"];
$domain = $_SERVER["CO_DOMAIN"];
$fn = $doc.$down; // Filename on server
$flist = array();
$eula = '';

if (file_exists($fn) and is_file($fn)) { // Requested download is file
	$search_dir = dirname($fn);
	$repl = dirname($down);
	$name_only = splitFilename(basename($down));
} elseif (is_dir($fn)) { // Requested download is directory
	$search_dir = $fn;
	$repl = $down;
	$name_only = array();
} else { // Requested download not found on server
	status_not_found();
}

$flist = getFilesList($search_dir);

if (!empty($name_only)) {
	$pattern = "/^".$name_only[0]."\.EULA\.txt.*/";
	$eula = findSpecialEULA($flist, $pattern);
}

if (is_file($fn)) {
	if (is_file($doc."/".$repl."/".$eula)) { // Special EULA found
		$theme = getTheme($eula, $down);
	} elseif (is_file($doc."/".$repl."/EULA.txt")) { // No special EULA found
		$theme = getTheme("EULA.txt", $down);
	} elseif (findSpecialEULA($flist, "/.*EULA.txt.*/")) {
		// If file is requested but no special EULA for it and no EULA.txt is present,
		// look for any EULA and if found decide that current file is not protected.
		status_ok($down, $domain);
	} else {
		status_forbidden($down);
	}
} elseif (is_dir($fn)) {
	if (empty($flist) or findSpecialEULA($flist, "/.*EULA.txt.*/")) { // Directory contains only subdirs or any EULA
		status_ok($down, $domain);
	} else { // No special EULA, no EULA.txt, no OPEN-EULA.txt found
		status_forbidden($down);
	}
} else {
	status_forbidden($down);
}

$template_content = file_get_contents($doc."/licenses/".$theme.".html");
$eula_content = file_get_contents($doc."/licenses/".$theme.".txt");

$out = str_replace("EULA.txt", $eula_content, $template_content);
echo $out;
?>
