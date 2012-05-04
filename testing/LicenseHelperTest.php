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
    touch("file_with_no_dot");
    touch("file.with.more.dots");
    touch("file_with_one.dot");
  }

  /**
   * Removes help files
   */
  protected function tearDown() 
  {
    unlink("test_link");
    unlink("file_with_no_dot");
    unlink("file_with_one.dot");
    unlink("file.with.more.dots");
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

    $expected_count = count(scandir(dirname(__FILE__))) - 2; // remove '.' and '..'
    $this->assertCount($expected_count, $file_list);
  }

  /**
   * Split filename with no dot
   */
  public function testSplitFilename_noDot()
  {
    $filename_array = LicenseHelper::splitFilename("file_with_no_dot");
    $this->assertCount(2, $filename_array);
    $this->assertEquals("file_with_no_dot", $filename_array[0]);
    $this->assertEmpty($filename_array[1]);
  }

  /**
   * Split filename with multiple dots
   */
  public function testSplitFilename_moreDots()
  {
    $filename_array = LicenseHelper::splitFilename("file.with.more.dots");
    $this->assertCount(2, $filename_array);
    $this->assertEquals("file.with.more", $filename_array[0]);
    $this->assertEquals("dots", $filename_array[1]);
  }

  /**
   * Split filename with one dot
   */
  public function testSplitFilename_oneDot()
  {
    $filename_array = LicenseHelper::splitFilename("file_with_one.dot");
    $this->assertCount(2, $filename_array);
    $this->assertEquals("file_with_one", $filename_array[0]);
    $this->assertEquals("dot", $filename_array[1]);
  }

}

?>