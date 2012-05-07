<?php

class LicenseHelperTest extends PHPUnit_Framework_TestCase
{

  /**
   * Includes test class, creates some help files for testing
   */
  protected function setUp()
  {
    require_once("../licenses/LicenseHelper.php");
    symlink(__FILE__, "test_link");
  }

  /**
   * Removes help files
   */
  protected function tearDown() 
  {
    unlink("test_link");
  }

  /**
   * Test with directory
   */
  public function testCheckFile_nonFile()
  {
    $this->assertFalse(LicenseHelper::checkFile(dirname(__FILE__)));
  }

  /**
   * Test with link
   */
  public function testCheckFile_link()
  {
    $this->assertTrue(LicenseHelper::checkFile("test_link"));
  }

  /**
   * Test with file
   */
  public function testCheckFile_file()
  {
    $this->assertTrue(LicenseHelper::checkFile(__FILE__));
  }

  /**
   * Get file list from a file
   */
  public function testGetFilesList_file()
  {
    $file_list = LicenseHelper::getFilesList(__FILE__);
    $this->assertEmpty($file_list);
  }

  /**
   * Get file list from a directory
   */
  public function testGetFilesList_dir()
  {
    $file_list = LicenseHelper::getFilesList(dirname(__FILE__));
    $this->assertNotEmpty($file_list);
    $this->assertContains(basename(__FILE__), $file_list);
    
    // Remove '.' and '..'.
    $expected_count = count(scandir(dirname(__FILE__))) - 2;
    $this->assertCount($expected_count, $file_list);
  }

  /**
   * Test with pattern which will not match any filename.
   */
  public function testFindFileByPattern_noMatch()
  {
    $file_list = array("test.txt", "new_file.pdf");
    $pattern = "/^abc/";
    $this->assertFalse(LicenseHelper::findFileByPattern($file_list, $pattern));
  }

  /**
   * Test with pattern which will match a filename.
   */
  public function testFindFileByPattern_match()
  {
    $file_list = array("test.txt", "new_file.pdf");
    $pattern = "/test/";
    $this->assertEquals("test.txt", LicenseHelper::findFileByPattern($file_list, $pattern));
  }

}

?>