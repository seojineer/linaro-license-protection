<?php

class BuildInfo
{
    private $text_array = array();
    private $fields_defined = array("Format-Version", "Files-Pattern",
        "Build-Name", "Theme", "License-Type", "OpenID-Launchpad-Teams",
        "Collect-User-Data", "License-Text");
    private $multiline_vars = array("License-Text");

    public function readFile($fn)
    {
        $field = '';
        $fp_read = 0;
        if (is_dir($fn) or !is_file($fn)) return false;
        $file = fopen($fn, "r") or exit("Unable to open file $fn!");
        // Get the 'Format-Version' field.
        $line = fgets($file);
        $fields = explode(":", $line, "2");
        $this->text_array[$fields[0]] = trim($fields[1]);
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
                $this->text_array[$fp] = $tmp_arr;
                unset($tmp_arr);
            }
        }
        fclose($file);

        return true;
    }

    public function getFormatVersion()
    {
        if (array_key_exists('Format-Version', $this->text_array))
            return $this->text_array["Format-Version"];
        else
            return false;
    }

    public function getBuildName()
    {
        if (array_key_exists('Build-Name', $this->text_array))
            return $this->text_array["Build-Name"];
        else
            return false;
    }

    public function getTheme()
    {
        if (array_key_exists('Theme', $this->text_array))
            return $this->text_array["Theme"];
        else
            return false;
    }

    public function getLicenseType()
    {
        if (array_key_exists('License-Type', $this->text_array))
            return $this->text_array["License-Type"];
        else
            return false;
    }

    public function getLaunchpadTeams()
    {
        if (array_key_exists('OpenID-Launchpad-Teams', $this->text_array))
            return $this->text_array["OpenID-Launchpad-Teams"];
        else
            return false;
    }

    public function getCollectUserData()
    {
        if (array_key_exists('Collect-User-Data', $this->text_array))
            return $this->text_array["Collect-User-Data"];
        else
            return false;
    }

    public function getLicenseText()
    {
        if (array_key_exists('License-Text', $this->text_array))
            return $this->text_array["License-Text"];
        else
            return false;
    }
}
