<?php

class BuildInfo
{
    private $build_info_array;
    private $fields_defined;
    private $multiline_vars;
    private $search_path;
    private $fname;
    private $file_info_array;

    public function __construct($fn)
    {
        $this->build_info_array = array();
        $this->file_info_array = array();
        $this->fields_defined = array("Format-Version", "Files-Pattern",
            "Build-Name", "Theme", "License-Type", "OpenID-Launchpad-Teams",
            "Collect-User-Data", "License-Text");
        $this->multiline_vars = array("License-Text");
        $this->search_path = dirname($fn);
        $this->fname = basename($fn);
        $this->build_info_file = $this->search_path."/BUILD-INFO.txt";
        $data = $this->readFile();
        if (is_array($data)) {
            $this->build_info_array = $this->parseData($data);
            $this->file_info_array = $this->getInfoForFile($this->fname);
        }
    }

    public function readFile()
    {
        $data = array();
        if (is_dir($this->build_info_file) or !is_file($this->build_info_file) or filesize($this->build_info_file) == 0) return false;
        $file = fopen($this->build_info_file, "r") or exit("Unable to open file $this->build_info_file!");
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
        foreach (array_keys($this->build_info_array) as $key)
            if ($key != 'Format-Version') {
                $files = glob($this->search_path."/".$key);
                foreach ($files as $file)
                    if ($file == $this->search_path."/".$fname)
                        return $this->build_info_array[$key];
            }
        return array();
    }

    public function getFormatVersion()
    {
        if (array_key_exists('Format-Version', $this->build_info_array))
            return $this->build_info_array["Format-Version"];
        else
            return false;
    }

    // Get value of specified field for corresponding file
    public function get($field)
    {
        if (array_key_exists($field, $this->file_info_array))
            return $this->file_info_array[$field];
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
