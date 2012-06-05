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
        $data = $this->readFile();
        if (is_array($data)) {
            $this->text_array = $this->parseData($data);
        }
    }

    public function readFile()
    {
        $data = array();
        if (is_dir($this->fname) or !is_file($this->fname) or filesize($this->fname) == 0) return false;
        $file = fopen($this->fname, "r") or exit("Unable to open file $this->fname!");
        while(!feof($file)) {
            $line = fgets($file);
            if (trim($line) == "")
                continue;
            $data[] = $line;
        }
        return $data;
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

    public function parseContinuation($lines, &$line_no) {
        $text = '';
        $total_lines = count($lines);
        while ($line_no < $total_lines &&
            strlen($lines[$line_no]) > 0) {
                if ($lines[$line_no][0] == ' ') {
                    $text .= "\n" . substr($lines[$line_no], 1);
                    $line_no++;
                } else {
                    break;
                }
            }
        return $text;
    }

    /**
     * `data` should be array of lines.
     */
    public function parseData($data) {
        if (!is_array($data)) {
            throw new InvalidArgumentException("No array provided.");
        }
        $format_line = array_shift($data);
        $values = $this->parseLine($format_line);
        if (!array_key_exists("Format-Version", $values)) {
            throw new InvalidArgumentException("Data in incorrect format.");
        }
        $result = array("Format-Version" => $values["Format-Version"]);

        $line_no = 0;
        while ($line_no < count($data)) {
            $line = $data[$line_no];
            $values = $this->parseLine($line);
            if (array_key_exists("Files-Pattern", $values)) {
                $line_no++;
                $block = $this->parseBlock($data, $line_no);
                if (is_array($block)) {
                    foreach (explode(",", $values["Files-Pattern"]) as $pattern) {
                        $result[$pattern] = $block;
                    }
                }
            }
        }
        return $result;
    }

    public function parseBlock($data, &$line_no) {
        $result = array();

        if (!is_array($data)) {
            throw new InvalidArgumentException("No array provided.");
        }
        while ($line_no < count($data)) {
            $line = $data[$line_no];
            $values = $this->parseLine($line);
            if (array_key_exists("License-Text", $values)) {
                $text = $values["License-Text"];
                $line_no++;
                $text .= $this->parseContinuation($data, $line_no);
                $result["License-Text"] = $text;
            } elseif (array_key_exists("Files-Pattern", $values)) {
                return $result;
            } else {
                $line_no++;
                $result = array_merge($result, $values);
            }
        }
        return $result;
    }
}
