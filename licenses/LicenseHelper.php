<?php

class LicenseHelper 
{

  // Get list of files into array to process them later.
  // Used to find special licenses and dirs with only subdirs.
  public static function checkFile($fn)
  {
    if (is_file($fn) or is_link($fn)) {
      return true;
    }
    return false;
  }

  public static function getFilesList($dirname)
  {
    $files = array(); 
    if ($handle = opendir($dirname)) {
      while ($handle && false !== ($entry = readdir($handle))) {
	if ($entry != "." && $entry != ".." && !is_dir($dirname."/".$entry) && $entry != "HEADER.html") {
	  $files[] = $entry;
	}
      }
    }
    closedir($handle);
    return $files;
  }

  // Get array of file name and extension from full filename.
  public static function splitFilename($filename)
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
  public static function findFileByPattern($fl, $pattern)
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
  public static function getTheme($eula, $down)
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

  public static function status_forbidden($dir)
  {
    header("Status: 403");
    header("HTTP/1.1 403 Forbidden");
    echo "<h1>Forbidden</h1>";
    echo "You don't have permission to access ".$dir." on this server.";
    exit;
  }

  public static function status_ok($dir, $domain)
  {
    header("Status: 200");
    header("Location: ".$dir);
    setcookie("redirectlicensephp", "yes", 0, "/", ".".$domain);
    exit;
  }

  public static function status_not_found()
  {
    header("Status: 404");
    header("HTTP/1.0 404 Not Found");
    echo "<h1>404 Not Found</h1>";
    echo "The requested URL was not found on this server.";
    exit;
  }

}