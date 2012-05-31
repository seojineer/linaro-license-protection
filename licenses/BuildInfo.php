<?php

class BuildInfo
{
    private $text_array = array();
    private $fields_defined = array("Format-Version", "Files-Pattern",
        "Build-Name", "Theme", "License-Type", "OpenID-Launchpad-Teams",
        "Collect-User-Data", "License-Text");
    private $multiline_vars = array("License-Text");
    private $search_path = '';
    private $fname = '';

    public function __construct($fn)
    {
        $this->search_path = dirname($fn);
        $this->fname = $fn;
        $this->readFile();
    }

    public function readFile()
    {
        $field = '';
        $fp_read = 0;
        if (is_dir($this->fname) or !is_file($this->fname) or filesize($this->fname) == 0) return false;
        $file = fopen($this->fname, "r") or exit("Unable to open file $this->fname!");
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
                $this->text_array[$fields[0]] = trim($fields[1]);
                $fp_read = 0;
            }
            $line = fgets($file);
            if (trim($line) == "")
                continue;
            $fields = explode(":", $line, "2");
            // Each block of fields begins with "Files-Pattern" field
            if ($fields[0] == "Files-Pattern") {
                $tmp_arr = array();
                $fp = trim($fields[1]);
                // Read next block of field by field
                while(!feof($file)) {
                    $line = fgets($file);
                    if (trim($line) == "")
                        continue;
                    $fields = explode(":", $line, "2");
                    // Read multiline field...
                    if (in_array($fields[0], $this->multiline_vars)) {
                        $field = $fields[0];
                        if (isset($fields[1]))
                            $tmp_arr[$fields[0]] = trim($fields[1]);
                        // ...until the EOF or...
                        while(!feof($file)) {
                            $line = fgets($file);
                            if (trim($line) == "")
                                continue;
                            $fields = explode(":", $line, "2");
                            // ...until we find next valid field
                            if(in_array($fields[0], $this->fields_defined)) {
                                // Start reading next block of fields
                                // if the field is "Files-Pattern"
                                if ($fields[0] == "Files-Pattern") {
                                    fseek($file, -(strlen($line)), SEEK_CUR);
                                    break 2;
                                }
                                // Or continue to process the next field
                                break;
                            }
                            $tmp_arr[$field] = $tmp_arr[$field].
                                "\n".rtrim($line);
                        }
                    }
                    // Save fields to the array
                    if (isset($fields[1])) {
                        $tmp_arr[$fields[0]] = trim($fields[1]);
                    }
                }
                // If there're several patterns, split them
                foreach(explode(",", $fp) as $pattern)
                    $this->text_array[$pattern] = $tmp_arr;
                unset($tmp_arr);
            }
        }
        fclose($file);

        return true;
    }

    private function getInfoForFile($fname)
    {
        /**
         * Get array of fields for corresponding file
         */
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

    // Get value of specified field for correspondong file
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

    public function parseLine($line) {
        $values = explode(":", $line, 2);
        if ($values === false || count($values) != 2) {
            throw new InvalidArgumentException("Line is not in the correct format.");
        } else {
            $field = trim($values[0]);
            $value = trim($values[1]);
            if (!$this->isValidField($field)) {
                throw new InvalidArgumentException("Field '$field' not allowed.");
            } else {
                return array($field => $value);
            }
        }
    }

    public function isValidField($field_name) {
        if (in_array($field_name, $this->fields_defined)) {
            return true;
        } else {
            return false;
        }
    }
}
