from BeautifulSoup import BeautifulSoup

from license_protected_file_downloader import LicenseProtectedFileFetcher


class EmptyDirectoryException(Exception):
    ''' Directory at the current URL is empty. '''


class NoLicenseException(Exception):
    ''' No license protecting the file. '''


class UnexpectedLicenseException(Exception):
    ''' License protecting non-licensed the file. '''


class DoctestProductionBrowser():
    """Doctest production testing browser class."""

    def __init__(self, host_address):
        self.host_address = host_address
        self.current_url = host_address
        self.fetcher = LicenseProtectedFileFetcher()

    def is_dir(self, link):
        """Check if the link is a directory."""
        return link[-1] == "/"

    def get_header(self):
        """Get header from the current url."""
        return self.parse_header(self.fetcher.get_headers(self.current_url))

    def get_license_text(self):
        """Get license from the current URL if it redirects to license."""
        license = self.fetcher.get_or_return_license(self.current_url)
        if license[0]:
            return license[0]
        else:
            raise NoLicenseException("License expected here.")

    def get_unprotected_file_header(self):
        """Get headers from unprotected file."""
        page = self.fetcher.get_or_return_license(self.current_url)
        # Check if license with accept and decline links is returned.
        if len(page) == 3:
            raise UnexpectedLicenseException("License not expected here.")
        else:
            return self.parse_header(self.fetcher.header)

    def get_content(self):
        """Get contents from the current url."""
        return self.fetcher.get(self.current_url)

    def get_content_title(self):
        """Get content title from the current url."""
        return self.get_title(self.fetcher.get(self.current_url))

    def get_header_when_redirected(self):
        """Get header when the client is redirected to the license."""
        self.fetcher.get(self.current_url)
        return self.parse_header(self.fetcher.header)

    def accept_license_get_header(self):
        """Accept license and get header of the file it redirects to."""
        license = self.fetcher.get_or_return_license(self.current_url)
        # Second element in result is the accept link.
        if license[1]:
            self.fetcher.get_protected_file(license[1], self.current_url)
            return self.parse_header(self.fetcher.header)
        else:
            raise NoLicenseException("License expected here.")

    def decline_license(self):
        """Decline license. Return title of the page."""
        return self.get_title(
            self.fetcher.get(self.current_url, accept_license=False)
            )

    def parse_header(self, header):
        """Formats headers from dict form to the multi-line string."""
        header_str = ""
        for key in sorted(header.iterkeys()):
            header_str += "%s: %s\n" % (key, header[key])
        return header_str

    def get_title(self, html):
        soup = BeautifulSoup(html)
        titles_all = soup.findAll('title')
        if len(titles_all) > 0:
            return titles_all[0].contents[0]
        else:
            return ""

    def browse_to_relative(self, path):
        """Change current url relatively."""
        self.current_url += path

    def browse_to_absolute(self, path):
        """Change current url to specified path."""
        self.current_url = self.host_address + path

    def browse_to_next(self, condition):
        """Browse to next dir/build file that matches condition.

        Set the current URL to to match the condition among the
        links in the current page with priority to build files.
        If there's no match, set link to build file if present.
        Otherwise, set link to first directory present.
        """
        links = self.find_links(self.get_content())
        link = self.find_link_with_condition(links, condition)
        if not link:
            # No link matching condition, get first build in list.
            link = self.find_build_tar_bz2(links)
        if not link:
            # Still no link, just get first dir in list.
            link = self.find_directory(links)
        if not link:
            # We found page with no directories nor builds.
            raise EmptyDirectoryException("Directory is empty.")

        self.browse_to_relative(link)

    def find_links(self, html):
        """Return list of links on the page with special conditions.

        Return all links below the "Parent directory" link.
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

    def find_link_with_condition(self, links, condition):
        """Finds a link which satisfies the condition.

        Condition is actually to contain the string from the list.
        Build files (which end in .tar.bz2) have the priority.
        """
        for link in links:
            if condition in link and link[-7:] == "tar.bz2":
                return link
        for link in links:
            if condition in link:
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
