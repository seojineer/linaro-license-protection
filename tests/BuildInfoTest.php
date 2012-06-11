<?php

require_once("licenses/BuildInfo.php");

class BuildInfoTest extends PHPUnit_Framework_TestCase
{

    private $temp_filename;
    private $good_bi;
    private $empty_bi;
    private $fname;

    public function setUp()
    {
        $this->good_bi = new BuildInfo("tests/BUILD-INFO.txt");
        $this->temp_filename = tempnam(sys_get_temp_dir(), "build-info");
        $this->empty_bi = new BuildInfo($this->temp_filename);
        $this->fname = "BUILD-INFO.txt";
    }

    public function tearDown() {
        if (file_exists($this->temp_filename)) {
            unlink($this->temp_filename);
        }
    }

    /**
     * @expectedException InvalidArgumentException
     */
    public function test_parseLine_fails() {
        $line = "no separator";
        $buildinfo = new BuildInfo("");
        $buildinfo->parseLine($line);
    }

    public function test_parseLine_passes() {
        $line = "Build-Name:value";
        $buildinfo = new BuildInfo("");
        $this->assertEquals(array("Build-Name" => "value"),
                            $buildinfo->parseLine($line));
    }

    public function test_parseLine_trims() {
        $line = "Build-Name: value";
        $buildinfo = new BuildInfo("");
        $this->assertEquals(array("Build-Name" => "value"),
                            $buildinfo->parseLine($line));
    }

    /**
     * @expectedException InvalidArgumentException
     */
    public function test_parseLine_invalid_field() {
        $line = "field: value";
        $buildinfo = new BuildInfo("");
        $this->assertEquals(array("field" => "value"),
                            $buildinfo->parseLine($line));
    }

    public function test_isValidField_true() {
        $buildinfo = new BuildInfo("");
        $fields_allowed = array("Format-Version", "Files-Pattern",
                                "Build-Name", "Theme", "License-Type", "OpenID-Launchpad-Teams",
                                "Collect-User-Data", "License-Text");
        foreach ($fields_allowed as $field) {
            $this->assertTrue($buildinfo->isValidField($field));
        }
    }

    public function test_isValidField_false() {
        $buildinfo = new BuildInfo("");
        $this->assertFalse($buildinfo->isValidField("Some random text"));
    }

    /**
     * @expectedException InvalidArgumentException
     */
    public function test_parseData_fails() {
        $buildinfo = new BuildInfo("");
        $buildinfo->parseData(array("Arbitrary text"));
    }

    /**
     * @expectedException InvalidArgumentException
     */
    public function test_parseData_array_expected() {
        $buildinfo = new BuildInfo("");
        $buildinfo->parseData("Arbitrary text");
    }

    public function test_parseData_format_version() {
        $buildinfo = new BuildInfo("");
        $values = $buildinfo->parseData(array("Format-Version: 2.0"));
        $this->assertEquals(array("Format-Version" => "2.0"),
                            $values);
    }

    public function test_parseData_extra_fields() {
        $buildinfo = new BuildInfo("");
        $values = $buildinfo->parseData(array(
                                              "Format-Version: 2.0",
                                              "Files-Pattern: *.txt",
                                              "Build-Name: woohoo"));
        $this->assertEquals(array("Format-Version" => "2.0",
                                  "*.txt" => array("Build-Name" => "woohoo")),
                            $values);
    }

    public function test_parseBlock_license() {
        $buildinfo = new BuildInfo("");
        $lineno = 0;
        $values = $buildinfo->parseBlock(array(
                                              "Format-Version: 2.0",
                                              "License-Text: line1",
                                              " line2"), $lineno);
        $this->assertEquals(array("Format-Version" => "2.0",
                                  "License-Text" => "line1\nline2"),
                            $values);
    }

    public function test_parseContinuation_no_continuation() {
        $buildinfo = new BuildInfo("");
        $lineno = 0;
        $this->assertEquals(
            "",
            $buildinfo->parseContinuation(array("no-space"), $lineno));
    }

    public function test_parseContinuation_indexed() {
        $buildinfo = new BuildInfo("");
        $lineno = 0;
        $this->assertEquals("",
                            $buildinfo->parseContinuation(array("no-space", " space"), $lineno));
    }

    public function test_parseContinuation() {
        $buildinfo = new BuildInfo("");
        $lineno = 1;
        $value = $buildinfo->parseContinuation(array("no-space", " line1", " line2"), $lineno);
        $this->assertEquals("\nline1\nline2", $value);
    }

    /**
     * @expectedException InvalidArgumentException
     */
    public function test_parseData_no_format_version_fails() {
        $buildinfo = new BuildInfo("");
        $values = $buildinfo->parseData(array("Build-Name: blah"));
    }

   public function test_parseData_blocks() {
        $buildinfo = new BuildInfo("");
        $lineno = 0;
        $values = $buildinfo->parseData(array("Format-Version: 2.0",
                                              "Files-Pattern: *.txt",
                                              "Build-Name: woohoo",
                                              "Files-Pattern: *.tgz",
                                              "Build-Name: weehee"));
        $this->assertEquals(array("Format-Version" => "2.0",
                                  "*.txt" => array("Build-Name" => "woohoo"),
                                  "*.tgz" => array("Build-Name" => "weehee")),
                            $values);
   }
 
    public function test_parseData_block_multiple_patterns() {
        $buildinfo = new BuildInfo("");
        $lineno = 0;
        $values = $buildinfo->parseData(array("Format-Version: 2.0",
                                              "Files-Pattern: *.txt,*.tgz",
                                              "Build-Name: weehee"));
        $this->assertEquals(array("Format-Version" => "2.0",
                                  "*.txt" => array("Build-Name" => "weehee"),
                                  "*.tgz" => array("Build-Name" => "weehee")),
                            $values);
    }
 
   
    /**
     * Running readFile on a directory returns false.
     */
    public function test_readFile_nonFile()
    {
        $bi = new BuildInfo(dirname(__FILE__));
        $this->assertFalse($bi->readFile());
    }

    /**
     * Running readFile on a nonexistent file returns false.
     */
    public function test_readFile_nonexistentFile()
    {
        $bi = new BuildInfo("nonexistent.file");
        $this->assertFalse($bi->readFile());
    }

    /**
     * Running readFile on a regular file returns array of strings.
     */
    public function test_readFile_file()
    {
        $bi = new BuildInfo("tests/BUILD-INFO.txt");
        $this->assertInternalType('array', $bi->readFile());
    }

    /**
     * Running 'get' functions on an empty fields returns false.
     */
    public function test_getFormatVersion_empty()
    {
        $this->assertFalse($this->empty_bi->getFormatVersion());
    }

    /**
     * Running 'get' functions on non-empty fields returns string value.
     */
    public function test_getFormatVersion_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getFormatVersion());
    }

    public function test_getFormatVersion()
    {
        $this->assertEquals('0.1', $this->good_bi->getFormatVersion());
    }

    public function test_getBuildName_empty()
    {
        $this->assertFalse($this->empty_bi->get("Build-Name"));
    }

    public function test_getBuildName_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->get("Build-Name"));
    }

    public function test_getBuildName()
    {
        $this->assertEquals(
            'landing-snowball', $this->good_bi->get("Build-Name"));
    }
}
?>
