<?php

class BuildInfo
{
    private $text_array = array();
    private $fields_defined = array("Format-Version", "Files-Pattern",
        "Build-Name", "Theme", "License-Type", "OpenID-Launchpad-Teams",
        "Collect-User-Data", "License-Text");
    private $multiline_vars = array("License-Text");
    private $search_path = '';

    public function readFile($fn)
    {
        $this->search_path = dirname($fn);
        $field = '';
        $fp_read = 0;
        if (is_dir($fn) or !is_file($fn) or filesize($fn) == 0) return false;
        $file = fopen($fn, "r") or exit("Unable to open file $fn!");
        // Get the 'Format-Version' field.
        $line = fgets($file);
        $fields = explode(":", $line, "2");
        if (isset($fields[1]))
            $this->text_array[$fields[0]] = trim($fields[1]);
        else
            $this->text_array[$fields[0]] = '';
        // Get the rest fileds.
        while(!feof($file)) {
            if ($fp_read) {
                print_r($fields);
                $this->text_array[$fields[0]] = trim($fields[1]);
                $fp_read = 0;
            }
            $line = fgets($file);
            if (trim($line) == "")
                continue;
            $fields = explode(":", $line, "2");
            if ($fields[0] == "Files-Pattern") {
                $tmp_arr = array();
                $fp = trim($fields[1]);
                while(!feof($file)) {
                    $line = fgets($file);
                    if (trim($line) == "")
                        continue;
                    $fields = explode(":", $line, "2");
                    if (in_array($fields[0], $this->multiline_vars)) {
                        $field = $fields[0];
                        if (isset($fields[1]))
                            $tmp_arr[$fields[0]] = trim($fields[1]);
                        while(!feof($file)) {
                            $line = fgets($file);
                            if (trim($line) == "")
                                continue;
                            $fields = explode(":", $line, "2");
                            if(in_array($fields[0], $this->fields_defined)) {
                                if ($fields[0] == "Files-Pattern") {
                                    fseek($file, -(strlen($line)), SEEK_CUR);
                                    break 2;
                                }
                                break;
                            }
                            $tmp_arr[$field] = $tmp_arr[$field].
                                "\n".rtrim($line);
                        }

                    }
                    if (isset($fields[1])) {
                        $tmp_arr[$fields[0]] = trim($fields[1]);
                    }
                }
                foreach(explode(",", $fp) as $pattern)
                    $this->text_array[$pattern] = $tmp_arr;
                unset($tmp_arr);
            }
        }
        fclose($file);

        return true;
    }

    private function getInfoForFile($fname) {
        foreach (array_keys($this->text_array) as $key)
            if ($key != 'Format-Version') {
                $files = glob($this->search_path."/".$key);
                foreach ($files as $file)
                    if ($file == $this->search_path."/".$fname)
                        return $this->text_array[$key];
            }
        return array();
    }

    public function getFormatVersion()
    {
        if (array_key_exists('Format-Version', $this->text_array))
            return $this->text_array["Format-Version"];
        else
            return false;
    }

    public function getBuildName($fname)
    {
        $info = $this->getInfoForFile($fname);
        if (array_key_exists('Build-Name', $info))
            return $info["Build-Name"];
        else
            return false;
    }

    public function getTheme($fname)
    {
        $info = $this->getInfoForFile($fname);
        if (array_key_exists('Theme', $info))
            return $info["Theme"];
        else
            return false;
    }

    public function getLicenseType($fname)
    {
        $info = $this->getInfoForFile($fname);
        if (array_key_exists('License-Type', $info))
            return $info["License-Type"];
        else
            return false;
    }

    public function getLaunchpadTeams($fname)
    {
        $info = $this->getInfoForFile($fname);
        if (array_key_exists('OpenID-Launchpad-Teams', $info))
            return $info["OpenID-Launchpad-Teams"];
        else
            return false;
    }

    public function getCollectUserData($fname)
    {
        $info = $this->getInfoForFile($fname);
        if (array_key_exists('Collect-User-Data', $info))
            return $info["Collect-User-Data"];
        else
            return false;
    }

    public function getLicenseText($fname)
    {
        $info = $this->getInfoForFile($fname);
        if (array_key_exists('License-Text', $info))
            return $info["License-Text"];
        else
            return false;
    }
}
