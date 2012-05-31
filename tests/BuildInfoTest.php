<?php

require_once("licenses/BuildInfo.php");

class BuildInfoTest extends PHPUnit_Framework_TestCase
{

    private $temp_filename;
    private $good_bi;
    private $empty_bi;
    private $fname;
    private $lic_text_test = 
        '<p>IMPORTANT — PLEASE READ THE FOLLOWING AGREEMENT CAREFULLY.</p>';

    public function __construct()
    {
        $this->good_bi = new BuildInfo("tests/BUILD-INFO.txt");
        $this->temp_filename = tempnam(sys_get_temp_dir(), "build-info");
        $this->empty_bi = new BuildInfo($this->temp_filename);
        $this->fname = "BUILD-INFO.txt";
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
                                              "Build-Name: woohoo"));
        $this->assertEquals(array("Format-Version" => "2.0",
                                  "Build-Name" => "woohoo"),
                            $values);
    }

    public function test_parseData_license() {
        $buildinfo = new BuildInfo("");
        $values = $buildinfo->parseData(array(
                                              "Format-Version: 2.0",
                                              "License-Text: line1",
                                              " line2"));
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
     * Running readFile on a regular file returns true.
     */
    public function test_readFile_file()
    {
        $bi = new BuildInfo("tests/BUILD-INFO.txt");
        $this->assertTrue($bi->readFile());
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
        $this->assertFalse($this->empty_bi->getBuildName($this->fname));
    }

    public function test_getBuildName_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getBuildName($this->fname));
    }

    public function test_getBuildName()
    {
        $this->assertEquals(
            'landing-snowball', $this->good_bi->getBuildName($this->fname));
    }

    public function test_getTheme_empty()
    {
        $this->assertFalse($this->empty_bi->getTheme($this->fname));
    }

    public function test_getTheme_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getTheme($this->fname));
    }

    public function test_getTheme()
    {
        $this->assertEquals(
            'stericsson', $this->good_bi->getTheme($this->fname));
    }

    public function test_getLicenseType_empty()
    {
        $this->assertFalse($this->empty_bi->getLicenseType($this->fname));
    }

    public function test_getLicenseType_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getLicenseType($this->fname));
    }

    public function test_getLicenseType()
    {
        $this->assertEquals(
            'open', $this->good_bi->getLicenseType($this->fname));
    }

    public function test_getCollectUserData_empty()
    {
        $this->assertFalse($this->empty_bi->getCollectUserData($this->fname));
    }

    public function test_getCollectUserData_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getCollectUserData($this->fname));
    }

    public function test_getCollectUserData()
    {
        $this->assertEquals(
            'yes', $this->good_bi->getCollectUserData($this->fname));
    }

    public function test_getLaunchpadTeams_empty()
    {
        $this->assertFalse($this->empty_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLaunchpadTeams_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLaunchpadTeams()
    {
        $this->assertEquals(
            'linaro,non-linaro',
            $this->good_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLicenseText_empty()
    {
        $this->assertFalse($this->empty_bi->getLicenseText($this->fname));
    }

    public function test_getLicenseText_type()
    {
        $this->assertInternalType(
            'string', $this->good_bi->getLicenseText($this->fname));
    }

    public function test_getLicenseText()
    {
        $this->assertStringStartsWith(
            $this->lic_text_test,
            $this->good_bi->getLicenseText($this->fname));
    }
}
?>
