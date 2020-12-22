#!/usr/bin/env python
# coding: utf-8

import os
import webapp2
import jinja2
import settings
import re

from google.appengine.api import urlfetch
from google.appengine.api import memcache
from xml.dom.minidom import parseString
from lxml import html


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class MainHandler(webapp2.RequestHandler):
    def get(self):
        """

        """
        ls_values = {
            "title": settings.app_title,
            "description": settings.app_description,
            "keywords": settings.app_keywords,
            "url": settings.app_url}

        lr_template = jinja_environment.get_template("main.html")
        self.response.out.write(lr_template.render(ls_values))


class RSSHandler(webapp2.RequestHandler):
    def get(self):
        """

        """
        l_xml = memcache.get(settings.rss_url)

        if l_xml is None:
            lr_response = urlfetch.fetch(settings.rss_url)
            l_xml = lr_response.content
            memcache.set(settings.rss_url, l_xml, settings.rss_timeout)

        lr_xml = parseString(l_xml)

        lr_channel = lr_xml.getElementsByTagName("channel")[0]

        lr_title = lr_channel.getElementsByTagName("title")[0]
        lr_title.childNodes[0].data = "Habrahabr"

        lr_link = lr_channel.getElementsByTagName("link")[0]
        lr_link.childNodes[0].data = settings.app_url + "/rss"

        lt_items = lr_channel.getElementsByTagName("item")

        for lr_item in lt_items:

            #lr_guid = lr_item.getElementsByTagName("guid")[0]
            #lr_guid.setAttribute("isPermaLink", "false")

            lr_link = lr_item.getElementsByTagName("link")[0]
            l_link = lr_link.childNodes[0].data.replace("habrahabr.ru", "m.habrahabr.ru")
            # lr_link.childNodes[0].data = l_link

            l_html = memcache.get(l_link)

            if l_html is None:
                lr_response = urlfetch.fetch(l_link)
                l_html = lr_response.content
                memcache.set(l_link, l_html, settings.link_timeout)

            lr_html = html.fromstring(l_html.decode("utf-8"))

            lr_div = lr_html.xpath('//*[@id="post_text"]')[0]

            l_div = html.tostring(lr_div).strip()

            lr_regexp = re.compile('^<div[^>]*>(.*)</div>$', re.IGNORECASE+re.DOTALL+re.MULTILINE)

            lr_match = lr_regexp.match(l_div)

            l_description = lr_match.group(1)

            l_description += u"<div><p><a href='{url}#comments'>{text}</a></p></div>".format(
                                url=l_link.replace("m.habrahabr.ru", "habrahabr.ru"),
                                text=u"Читать комментарии →")

            lr_description = lr_item.getElementsByTagName("description")[0]

            if len(lr_description.childNodes) != 0:
                lr_description.childNodes[0].data = l_description

            # lr_text = lr_description.createTextNode()
            # lr_description.appendChild(lr_text)

        self.response.out.write(lr_xml.toxml("utf-8"))

app = webapp2.WSGIApplication([
    ("/", MainHandler),
    ("/rss", RSSHandler)],
    debug=True)