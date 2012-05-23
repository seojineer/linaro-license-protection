<?php

class BuildInfo
{
    private $text_array = array();
    private $multiline_vars = array("License-Text");

    public function readFile($fn)
    {
        $field = '';
        if (is_dir($fn) or !is_file($fn)) return false;
        $file = fopen($fn, "r") or exit("Unable to open file $fn!");
        while(!feof($file)) {
            $line = fgets($file);
            if (trim($line) == "")
                continue;
            $fields = explode(":", $line, "2");
            if (isset($fields[1])) {
                $field = $fields[0];
                $this->text_array[$field] = trim($fields[1]);
            }
            elseif (in_array($field, $this->multiline_vars)) {
                while(!feof($file)) {
                    $line = fgets($file);
                    $this->text_array[$field] = $this->text_array[$field]."\n".rtrim($line);
                }
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
