<?php

class LicenseHelperTest extends PHPUnit_Framework_TestCase
{

    private $temp_filename;

    /**
     * Include test class, create some help files for testing.
     */
    protected function setUp()
    {
        require_once("../licenses/LicenseHelper.php");
        $this->temp_filename = tempnam(dirname(__FILE__), "unittest");
    }


    /**
     * Remove helper files used in testing.
     */
    protected function tearDown()
    {
        unlink($this->temp_filename);
    }

    /**
     * Running checkFile on a directory path returns false.
     */
    public function test_checkFile_nonFile()
    {
        $this->assertFalse(LicenseHelper::checkFile(dirname(__FILE__)));
    }

    /**
     * Running checkFile on a symbolic link to an existing file returns true.
     */
    public function test_checkFile_link()
    {
        try {
            symlink($this->temp_filename, "test_link");
            $this->assertTrue(LicenseHelper::checkFile("test_link"));
            unlink("test_link");
            // PHP doesn't support finally block, ergo using this hack.
        } catch (Exception $e) {
            unlink("test_link");
            throw $e;
        }
    }

    /**
     * Running checkFile on a regular file returns true.
     */
    public function test_checkFile_file()
    {
        $this->assertTrue(LicenseHelper::checkFile(__FILE__));
    }

    /**
     * getFileList throws an InvalidArgumentException when passed
     * an argument pointing to a file.
     * @expectedException InvalidArgumentException
     */
    public function test_getFilesList_file()
    {
        $file_list = LicenseHelper::getFilesList(__FILE__);
    }

    /**
     * getFileList returns a list of filenames in that directory.
     */
    public function test_getFilesList_dir()
    {
        $temp_dir_name = tempnam(dirname(__FILE__), "unittest");
        if (file_exists($temp_dir_name)) {
            unlink($temp_dir_name);
        }
        mkdir($temp_dir_name);

        $temp_file_name_1 = tempnam($temp_dir_name, "unittest");
        $temp_file_name_2 = tempnam($temp_dir_name, "unittest");

        try {
            $file_list = LicenseHelper::getFilesList($temp_dir_name);
            $this->assertCount(2, $file_list);

            $this->assertEquals(basename($temp_file_name_1), $file_list[0]);
            $this->assertEquals(basename($temp_file_name_2), $file_list[1]);

            unlink($temp_file_name_1);
            unlink($temp_file_name_2);
            rmdir($temp_dir_name);
            // PHP doesn't support finally block, ergo using this hack.
        } catch (Exception $e) {
            unlink($temp_file_name_1);
            unlink($temp_file_name_2);
            rmdir($temp_dir_name);
            throw $e;
        }
    }

    /**
     * Running findFileByPattern on an array without matches returns false.
     */
    public function test_findFileByPattern_noMatch()
    {
        $file_list = array("test.txt", "new_file.pdf");
        $pattern = "/^abc/";
        $this->assertFalse(
            LicenseHelper::findFileByPattern($file_list, $pattern));
    }

    /**
     * Running findFileByPattern on an array with matches returns first
     * matching element.
     */
    public function test_findFileByPattern_match()
    {
        $file_list = array("test.txt", "new_file.pdf");
        $pattern = "/test/";
        $this->assertEquals("test.txt",
                            LicenseHelper::findFileByPattern($file_list,
                                                             $pattern));
    }

    /**
     * getTheme returns a generic Linaro-branded template when
     * no EULA is present (indicated by eula filename being named
     * EULA.txt or not).
     */
    public function test_getTheme_noEula_snowball()
    {
        $eula = "EULA.txt";
        $filename = "snowball.build.tar.bz2";
        $this->assertEquals("ste", LicenseHelper::getTheme($eula, $filename));
    }

    /**
     * getTheme returns a generic Linaro-branded template when
     * no EULA is present (indicated by eula filename being named
     * EULA.txt or not).
     */
    public function test_getTheme_noEula_origen()
    {
        $eula = "EULA.txt";
        $filename = "origen.build.tar.bz2";
        $this->assertEquals("samsung",
                            LicenseHelper::getTheme($eula, $filename));
    }

    /**
     * getTheme returns a generic Linaro-branded template when
     * no EULA is present (indicated by eula filename being named
     * EULA.txt or not).
     */
    public function test_getTheme_noEula_generic()
    {
        $eula = "EULA.txt";
        $filename = "build.tar.bz2";
        $this->assertEquals("linaro",
                            LicenseHelper::getTheme($eula, $filename));
    }

    /**
     * Running geTheme with eula file present (indicated by eula filename
     * being named EULA.txt or not) returns extension of eula file.
     */
    public function test_getTheme_eula()
    {
        $eula = "EULA.txt.test";
        $this->assertEquals("test", LicenseHelper::getTheme($eula, ""));
    }

}

?>