from models.Story import Story
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from MainProcess import MainProcess
import config


class Parser(MainProcess):
    """
    Performs the actual digging through the HTML and retrieval of story params
    """
    scan_record = None
    headline_links = []

    def __init__(self):
        """
        Constrictor : Sets the important html element setting needed for parsing
        :param scan_record: Scan record tha contains the names of the html tags and other info that we will use to get
        the story data
        """
        super(Parser, self).__init__()

    def setScanRecord(self, scan_record):
        self.scan_record = scan_record

    def buildSoupAttrs(self, tag_type):
        """
        Set the bs4 soup object based on properties present in the scan record
        :param tag_type: the type of the tag we are using
        :return: soup_attrs dict
        """
        soup_attrs = {}
        # Set soup strainer attributes if present in object
        if getattr(self.scan_record, tag_type + '_class') not in [None, '']:
            soup_attrs['class'] = getattr(self.scan_record, tag_type + '_class')
        if getattr(self.scan_record, tag_type + '_element_id') not in [None, '']:
            soup_attrs['id'] = getattr(self.scan_record, tag_type + '_element_id')
        if getattr(self.scan_record, tag_type + '_extra_attribute_1_name') not in [None, ''] and \
           getattr(self.scan_record, tag_type + '_extra_attribute_1_value') not in [None, '']:
            soup_attrs[getattr(self.scan_record, tag_type + '_extra_attribute_1_name')] = \
                getattr(self.scan_record, tag_type + '_extra_attribute_1_value')
        if getattr(self.scan_record, tag_type + '_extra_attribute_2_name') not in [None, ''] and \
           getattr(self.scan_record, tag_type + '_extra_attribute_2_value') not in [None, '']:
            soup_attrs[getattr(self.scan_record, tag_type + '_extra_attribute_2_name')] = \
                getattr(self.scan_record, tag_type + '_extra_attribute_2_value')

        return soup_attrs

    def getTagData(self, tag_container, tag_type):
        """
        Get the tag data by first obtaining the tag from its container and then
        Getting the tag data from the correct attribute where it is stored
        :param tag_container: The soup object containing the tag
        :param tag_type: the type of the tag we are using
        :return: String data object that the tag contained
        """
        if tag_container is None:
            return None

        tag = tag_container.find(getattr(self.scan_record, tag_type + '_type'),
                                 self.buildSoupAttrs(tag_type))
        if tag is None:
            return None
        # Remove the dag from the soup
        tag.extract()

        data_attribute_name = getattr(self.scan_record, tag_type + '_data_attribute_name')

        if data_attribute_name == 'string' or data_attribute_name == 'text':
            data = unicode(getattr(tag, data_attribute_name))
        else:
            data = tag.get(data_attribute_name)

        return data

    def parseMainPage(self, response):
        """
        [2]
        Parse the main page response and extract the linkes
        :param response:
        :return: list of strings
        """
        headline_links = []

        strainer = SoupStrainer(self.scan_record.main_page_container_type,
                                self.buildSoupAttrs('main_page_container'))
        soup = BeautifulSoup(response, 'html.parser', parse_only=strainer)

        self.log('\nParsing Main Page ---------------------------------------------------------------', 'dev')
        self.log(soup.prettify(), 'debug')
        self.log(self.scan_record.main_page_container_type, 'dev')
        self.log(self.buildSoupAttrs('main_page_container'), 'dev')

        headline_links.append(self.parseFirstHeadlineLink(soup))
        headline_links += self.parseHeadlineLinks(soup)

        self.log('\nHeadline Link Count: %s' % len(headline_links), 'dev')

        return headline_links

    def parseFirstHeadlineLink(self, soup):
        """
        [2.1]
        Parse the main features stroy link on the page. It is usually wrapped in a different container than the others
        :param soup: BeautifulSoup object
        :return:
        """
        self.log('\nParsing First Headline Link ---------------------------------------------------------------', 'dev')
        self.log(soup.prettify(), 'debug')
        self.log(self.scan_record.first_headline_container_type, 'dev')
        self.log(self.buildSoupAttrs('first_headline_container'), 'dev')

        link_container = soup.find(self.scan_record.first_headline_container_type,
                                   self.buildSoupAttrs('first_headline_container'))

        first_link = self.getTagData(link_container, 'first_headline')

        return first_link

    def parseHeadlineLinks(self, soup):
        """
        [2.2]
        Parse the regular headline links
        :param soup: BeautifulSoup object
        :return:
        """

        self.log('\nParsing Headline Links ---------------------------------------------------------------------', 'dev')
        self.log(soup.prettify(), 'debug')
        self.log(self.scan_record.headline_container_type, 'dev')
        self.log(self.buildSoupAttrs('headline_container'), 'dev')

        headline_links = []

        link_containers = soup.find_all(self.scan_record.headline_container_type,
                                        self.buildSoupAttrs('headline_container'))

        for link_container in link_containers:
            link = self.getTagData(link_container, 'headline')

            headline_links.append(link)

        return headline_links

    def parseArticlePage(self, response):
        """
        [5]
        Parse the article page and gather the story data
        Create and populate a Story object
        :param response: html string
        :param scan_record: ScanRecord object - just used to get the source_is into the Story object
        :return: Story object
        """
        story = Story()

        story.source_id = self.scan_record.source_id

        strainer = SoupStrainer(self.scan_record.article_page_container_type,
                                self.buildSoupAttrs('article_page_container'))

        soup = BeautifulSoup(response, 'html.parser', parse_only=strainer)

        self.log('\nParsing Article Page ---------------------------------------------------------------------', 'dev')
        self.log(soup.prettify(), 'debug')
        self.log(self.scan_record.article_page_container_type, 'dev')
        self.log(self.buildSoupAttrs('article_page_container'), 'dev')

        article_elements = [{'prop': 'title', 'container': 'article_title_container', 'tag': 'article_title'},
                            {'prop': 'author', 'container': 'article_author_container', 'tag': 'article_author'},
                            {'prop': 'body', 'container': 'article_body_container', 'tag': 'article_body'}]
        for element in article_elements:
            if getattr(self.scan_record, element['container'] + '_type') is not None:
                tag_container = soup.find(getattr(self.scan_record, element['container'] + '_type'),
                                          self.buildSoupAttrs(element['container']))
            else:
                tag_container = soup

            tag_data = self.getTagData(tag_container, element['tag'])
            setattr(story, element['prop'], tag_data)

        if story.body:
            story.body = story.body[:config.settings['limits']['snippet_char_limit']-3] + '...'

        self.log(story.__dict__, 'dev')
        story.snippet = story.body

        # Set a story to active only if we got good data. The story url is set late in the controller
        if story.title and story.body:
            story.active = True
        else:
            story.active = False
        # Set author as a blank string to avoid db warning
        if story.author is None:
            story.author = ''

        return story


