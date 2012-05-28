<?php

require_once("licenses/BuildInfo.php");

class BuildInfoTest extends PHPUnit_Framework_TestCase
{

    private $temp_filename;
    private $good_bi;
    private $bi;
    private $fname;

    public function __construct()
    {
        $this->good_bi = new BuildInfo();
        $this->good_bi->readFile("tests/BUILD-INFO.txt");
        $this->temp_filename = tempnam(sys_get_temp_dir(), "build-info");
        $this->bi = new BuildInfo();
        $this->bi->readFile($this->temp_filename);
        $this->fname = "BUILD-INFO.txt";
    }

    /**
     * Running readFile on a directory fnameh returns false.
     */
    public function test_readFile_nonFile()
    {
        $this->assertFalse(BuildInfo::readFile(dirname(__FILE__)));
    }

    /**
     * Running readFile on a nonexistent file returns false.
     */
    public function test_readFile_nonexistentFile()
    {
        $this->assertFalse(BuildInfo::readFile("nonexistent.file"));
    }

    /**
     * Running readFile on a regular file returns true.
     */
    public function test_readFile_file()
    {
        $bi = new BuildInfo();
        $this->assertTrue($bi->readFile("tests/BUILD-INFO.txt"));
    }

    /**
     * Running 'get' functions on an empty fields returns false.
     */
    public function test_getFormatVersion_empty()
    {
        $this->assertFalse($this->bi->getFormatVersion());
    }

    /**
     * Running 'get' functions on non-empty fields returns string value.
     */
    public function test_getFormatVersion()
    {
        $this->assertInternalType('string', $this->good_bi->getFormatVersion());
    }

    public function test_getBuildName_empty()
    {
        $this->assertFalse($this->bi->getBuildName($this->fname));
    }

    public function test_getBuildName()
    {
        $this->assertInternalType('string', $this->good_bi->getBuildName($this->fname));
    }

    public function test_getTheme_empty()
    {
        $this->assertFalse($this->bi->getTheme($this->fname));
    }

    public function test_getTheme()
    {
        $this->assertInternalType('string', $this->good_bi->getTheme($this->fname));
    }

    public function test_getLicenseType_empty()
    {
        $this->assertFalse($this->bi->getLicenseType($this->fname));
    }

    public function test_getLicenseType()
    {
        $this->assertInternalType('string', $this->good_bi->getLicenseType($this->fname));
    }

    public function test_getCollectUserData_empty()
    {
        $this->assertFalse($this->bi->getCollectUserData($this->fname));
    }

    public function test_getCollectUserData()
    {
        $this->assertInternalType('string', $this->good_bi->getCollectUserData($this->fname));
    }

    public function test_getLaunchpadTeams_empty()
    {
        $this->assertFalse($this->bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLaunchpadTeams()
    {
        $this->assertInternalType('string', $this->good_bi->getLaunchpadTeams($this->fname));
    }

    public function test_getLicenseText_empty()
    {
        $this->assertFalse($this->bi->getLicenseText($this->fname));
    }

    public function test_getLicenseText()
    {
        $this->assertInternalType('string', $this->good_bi->getLicenseText($this->fname));
    }
}
?>
