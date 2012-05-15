#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup

from license_protected_file_downloader import LicenseProtectedFileFetcher

class DoctestProductionHelper():
    """Doctest production testing helper class."""

    def __init__(self, host_address):
        self.host_address = host_address
        self.fetcher = LicenseProtectedFileFetcher()

    def get_url_from_link(self, link):
        """Append link to host and return it."""
        return self.host_address + "/" + link

    def is_dir(self, link):
        """Check if the link has the slash as last char, thus pointing to the
        directory.

        """
        return link[-1] == "/"

    def find_links(self, html):
        """Return list of links on the page below the "Parent directory" link.
        Return whole list if there is no such link.

        """
        soup = BeautifulSoup(html)
        links_all = soup.findAll('a')
        had_parent = False
        links = []
        for link in links_all:
            if had_parent:
                links.append(link.get("href"))
            if link.contents[0] == "Parent Directory":
                had_parent = True

        if had_parent:
            return links
        else:
            return [each.get('href') for each in links_all]

    def follow_links_to_file(self, next_link, guidelines):
        """Use filefetcher to open links in the directory structure
        on a specified host until the build file is reached.

        Always open the first link in the list which is a directory
        and follows the guidelines criteria if possible.

        """
        next_link_is_dir = True
        while (next_link_is_dir):
            page = self.fetcher.get(self.get_url_from_link(next_link))
            links = self.find_links(page)
            # Find link which satisfies the given guidelines.
            good_link = self.find_directory_with_condition(links, guidelines)
            if not good_link:
                # No link matching criteria, just get first dir in list.
                good_link = self.find_directory(links)
            if not good_link:
                # Still no good link, must be we are in the builds directory.
                good_link = self.find_build_tar_bz2(links)
                next_link_is_dir = False
            if not good_link:
                # We found page with no directories nor builds.
                return None

            next_link += good_link

        return next_link

    def find_directory_with_condition(self, links, guidelines):
        """Finds a directory among list of links which satisfies the first
        condition in the guidelines list.
        Condition is actually to contain the string from the list.

        It also removes the matching string from guidelines so it's not used
        again in next iteration.

        """
        for link in links:
            if self.is_dir(link):
               for element in guidelines:
                   if element in link:
                       guidelines.remove(element)
                       return link
        return None

    def find_directory(self, links):
        """Finds a directory among list of links."""
        for link in links:
            if self.is_dir(link):
                return link
        return None

    def find_build_tar_bz2(self, links):
        """Finds a file list of links which ends in tar.bz2."""
        for link in links:
            if link[-7:] == "tar.bz2":
                return link
        return None

def main():
    helper = DoctestProductionHelper("http://snapshots.linaro.org")
    helper.follow_links_to_file("/",["android/","android/","snowball"])


if __name__ == "__main__":
    main()

