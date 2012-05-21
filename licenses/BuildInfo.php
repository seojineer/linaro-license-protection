<?php

class BuildInfo
{
    private $text_array = array();
    private $multiline_vars = array("License-Text");

    public function __construct($text_file)
    {
        if (file_exists($text_file)) {
            $this->text_array = $this->readFile($text_file);
        }
        else {
            throw new Exception("File $text_file not found");
        }
    }

    private function readFile($fn)
    {
        $text_ar = array();
        $field = '';
        $file = fopen($fn, "r") or exit("Unable to open file $fn!");
        while(!feof($file)) {
            $line = fgets($file);
            if (trim($line) == "")
                continue;
            $fields = explode(":", $line, "2");
            if (isset($fields[1])) {
                $field = $fields[0];
                $text_ar[$field] = trim($fields[1]);
            }
            elseif (in_array($field, $this->multiline_vars)) {
                while(!feof($file)) {
                    $line = fgets($file);
                    $text_ar[$field] = $text_ar[$field]."\n".rtrim($line);
                }
            }
        }
        fclose($file);

        return $text_ar;
    }

    public function getFormatVersion()
    {
        return $this->text_array["Format-Version"];
    }

    public function getBuildName()
    {
        return $this->text_array["Build-Name"];
    }

    public function getTheme()
    {
        return $this->text_array["Theme"];
    }

    public function getLicenseType()
    {
        return $this->text_array["License-Type"];
    }

    public function getLaunchpadTeams()
    {
        $this->text_array["OpenID-Launchpad-Teams"];
    }

    public function getCollectUserData()
    {
        return $this->text_array["Collect-User-Data"];
    }

    public function getLicenseText()
    {
        return $this->text_array["License-Text"];
    }
}
