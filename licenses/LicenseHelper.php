<?php

class LicenseHelper
{

    /**
     * Get list of files into array to process them later.
     * Used to find special licenses and dirs with only subdirs.
     */
    public static function checkFile($fn)
    {
        if (is_file($fn) or is_link($fn)) {
            return true;
        }
        return false;
    }

    /**
     * Get list of filenames from a directory
     */
    public static function getFilesList($dirname)
    {
        if (!is_dir($dirname)) {
            throw new InvalidArgumentException('Method argument '.
                                               'should be a directory path');
        }

        $files = array();
        if ($handle = opendir($dirname)) {
            while ($handle && false !== ($entry = readdir($handle))) {
                if ($entry != "." && $entry != ".." &&
                    !is_dir($dirname."/".$entry) && $entry != "HEADER.html") {
                    $files[] = $entry;
                }
            }
        }
        closedir($handle);
        return $files;
    }

    /**
     * Find a matching filename in an array from given filename template.
     */
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

    /**
     * Get license theme name from EULA filename.
     */
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

    public static function redirect_with_status($dir, $domain, $status)
    {
     	static $http = array (
	     200 => "HTTP/1.1 200 OK",
	     403 => "HTTP/1.1 403 Forbidden",
	     404 => "HTTP/1.1 404 Not Found"
     	);
        header($http[$status]);
        header ("Location: $dir");
        header("Status: ".$status);
	setcookie("redirectlicensephp", $status, 0, "/", ".".$domain);
        exit;
    }
}

