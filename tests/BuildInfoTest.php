<?php

require_once("licenses/BuildInfo.php");

class BuildInfoTest extends PHPUnit_Framework_TestCase
{

    private $temp_filename;
    private $good_bi;
    private $empty_bi;
    private $fname;
    private $lic_text_test = '<p>IMPORTANT — PLEASE READ THE FOLLOWING AGREEMENT CAREFULLY.</p>';

    public function __construct()
    {
        $this->good_bi = new BuildInfo("tests/BUILD-INFO.txt");
        $this->temp_filename = tempnam(sys_get_temp_dir(), "build-info");
        $this->empty_bi = new BuildInfo($this->temp_filename);
        $this->fname = "BUILD-INFO.txt";
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
        $this->assertInternalType('string', $this->good_bi->getFormatVersion());
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
        $this->assertInternalType('string', $this->good_bi->getBuildName($this->fname));
    }

    public function test_getBuildName()
    {
        $this->assertEquals('landing-snowball', $this->good_bi->getBuildName($this->fname));
    }

    public function test_getTheme_empty()
    {
        $this->assertFalse($this->empty_bi->getTheme($this->fname));
    }

    public function test_getTheme_type()
    {
        $this->assertInternalType('string', $this->good_bi->getTheme($this->fname));
    }

    public function test_getTheme()
    {
        $this->assertEquals('stericsson', $this->good_bi->getTheme($this->fname));
    }

    public function test_getLicenseType_empty()
    {
        $this->assertFalse($this->empty_bi->getLicenseType($this->fname));
    }

    public function test_getLicenseType_type()
    {
        $this->assertInternalType('string', $this->good_bi->getLicenseType($this->fname));
    }

    public function test_getLicenseType()
    {
        $this->assertEquals('open', $this->good_bi->getLicenseType($this->fname));
    }

    public function test_getCollectUserData_empty()
    {
        $this->assertFalse($this->empty_bi->getCollectUserData($this->fname));
    }

    public function test_getCollectUserData_type()
    {
        $this->assertInternalType('string', $this->good_bi->getCollectUserData($this->fname));
    }

    public function test_getCollectUserData()
    {
        $this->assertEquals('yes', $this->good_bi->getCollectUserData($this->fname));
    }

    public function test_getLaunchpadTeams_empty()
    {
        $this->assertFalse($this->empty_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLaunchpadTeams_type()
    {
        $this->assertInternalType('string', $this->good_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLaunchpadTeams()
    {
        $this->assertEquals('linaro,non-linaro', $this->good_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLicenseText_empty()
    {
        $this->assertFalse($this->empty_bi->getLicenseText($this->fname));
    }

    public function test_getLicenseText_type()
    {
        $this->assertInternalType('string', $this->good_bi->getLicenseText($this->fname));
    }

    public function test_getLicenseText()
    {
        $this->assertStringStartsWith($this->lic_text_test, $this->good_bi->getLicenseText($this->fname));
    }
}
?>
