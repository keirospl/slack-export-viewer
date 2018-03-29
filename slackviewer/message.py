from __future__ import unicode_literals

import datetime
import logging
import re
import os

import emoji
import markdown2

import urllib.request


class Message(object):
    def __init__(self, USER_DATA, CHANNEL_DATA, message, channel_name):
        self.__USER_DATA = USER_DATA
        self.__CHANNEL_DATA = CHANNEL_DATA
        self._message = message
        self._channel_name = channel_name

    ##############
    # Properties #
    ##############

    @property
    def user_id(self):
        return self._message["user"]

    @property
    def username(self):
        try:
            return self.__USER_DATA[self._message["user"]]["name"]
        except KeyError:
            # In case this is a bot or something, we fallback to "username"
            if "username" in self._message:
                return self._message["username"]
            # If that fails to, it's probably USLACKBOT...
            elif "user" in self._message:
                return self.user_id
            elif "bot_id" in self._message:
                return self._message["bot_id"]
            else:
                return None

    @property
    def time(self):
        # Handle this: "ts": "1456427378.000002"
        tsepoch = float(self._message["ts"].split(".")[0])
        return str(datetime.datetime.fromtimestamp(tsepoch)).split('.')[0]

    @property
    def msg(self):
        message = []

        text = self._message.get("text")
        if text:
            text = self._render_text(text)
            message.append(text)

        attachments = self._message.get("attachments", [])
        if attachments is not None:
            for att in attachments:
                message.append("")
                if "pretext" in att:
                    pretext = self._render_text(att["pretext"].strip())
                    message.append(pretext)
                if "title" in att:
                    title = self._render_text("**{}**".format(
                        att["title"].strip()
                    ))
                    message.append(title)
                if "text" in att:
                    text = self._render_text(att["text"].strip())
                    message.append(text)

        if self._message.get('subtype', None) == 'file_share':
            thefile = self._message['file']
            minetype = thefile['mimetype']
            if minetype.split('/')[0] == 'image':
                isimage = True
            else:
                isimage = False
            url = thefile['url_private']
            
            file_to_save = url
            
            if not thefile['is_external']:
                url_download = thefile['url_private_download']
            
                #download file
            
                if not os.path.exists("files"):
                    os.makedirs("files")
            
                if not os.path.exists(os.path.join("files", self._channel_name)):
                    os.makedirs(os.path.join("files", self._channel_name))
        
                filename, file_extension = os.path.splitext(thefile['name'])
                if file_extension is None or file_extension == "" or file_extension == ".(null)":
                    file_to_save = os.path.join("files", self._channel_name, "{}.{}".format(thefile['id'], thefile['filetype']))
                else:
                    file_to_save = os.path.join("files", self._channel_name, "{}{}".format(thefile['id'], file_extension))
                if not os.path.exists(file_to_save):
                    urllib.request.urlretrieve(url_download, file_to_save)
                    print("{}".format(file_to_save))
            
                #download file
            
            message.append('<a href="{}">Download File: {}</a>'.format(file_to_save, thefile['name']))

            if isimage:
                message.append('<img class="file" src="%s">' % file_to_save)

        if self._message.get('subtype', None) == 'file_comment':
            comment = self._message['comment']
            comment_text = comment['comment']
            #message.append(self._render_text(comment_text))
            message.append('<br /> %s' % comment_text)

        if message:
            if not message[0].strip():
                message = message[1:]
        return "<br />".join(message).strip()


    @property
    def img(self):
        try:
            size = "72"
            url = self.__USER_DATA[self._message["user"]]["profile"]["image_72"]
            filename, file_extension = os.path.splitext(url)
            file_to_save = os.path.join("avatars", size, "{}_{}{}".format(self._message["user"], size, file_extension))
            return file_to_save
        except KeyError:
            return "avatars/72/U11656PFZ_72.png"

    @property
    def id(self):
        return self.time

    ###################
    # Private Methods #
    ###################

    def _render_text(self, message):
        message = message.replace("<!channel>", "@channel")
        message = self._slack_to_accepted_emoji(message)
        # Handle "<@U0BM1CGQY|calvinchanubc> has joined the channel"
        message = re.sub(r"<@U\d\w+\|[A-Za-z0-9.-_]+>",
                         self._sub_annotated_mention, message)
        # Handle "<@U0BM1CGQY>"
        message = re.sub(r"<@U\d\w+>", self._sub_mention, message)
        # Handle links
        message = re.sub(
            # http://stackoverflow.com/a/1547940/1798683
            # TODO This regex is likely still incomplete or could be improved
            r"<(https|http|mailto):[A-Za-z0-9_\.\-\/\|\?\,\=\#\:\@]+>",
            self._sub_hyperlink, message
        )
        # Handle hashtags (that are meant to be hashtags and not headings)
        message = re.sub(r"(^| )#[A-Za-z0-9\.\-\_]+( |$)",
                         self._sub_hashtag, message)
        # Handle channel references
        message = re.sub(r"<#C0\w+>", self._sub_channel_ref, message)
        # Handle italics (convert * * to ** **)
        message = re.sub(r"(^| )\*[A-Za-z0-9\-._ ]+\*( |$)",
                         self._sub_bold, message)
        # Handle italics (convert _ _ to * *)
        message = re.sub(r"(^| )_[A-Za-z0-9\-._ ]+_( |$)",
                         self._sub_italics, message)

        # Escape any remaining hash characters to save them from being turned
        #  into headers by markdown2
        message = message.replace("#", "\\#")

        message = markdown2.markdown(
            message,
            extras=[
                "cuddled-lists",
                # Disable parsing _ and __ for em and strong
                # This prevents breaking of emoji codes like :stuck_out_tongue
                #  for which the underscores it liked to mangle.
                # We still have nice bold and italics formatting though
                #  because we pre-process underscores into asterisks. :)
                "code-friendly",
                "fenced-code-blocks",
                "pyshell"
            ]
        ).strip()
        # markdown2 likes to wrap everything in <p> tags
        if message.startswith("<p>") and message.endswith("</p>"):
            message = message[3:-4]

        # Newlines to breaks
        # Special handling cases for lists
        message = message.replace("\n\n<ul>", "<ul>")
        message = message.replace("\n<li>", "<li>")
        # Indiscriminately replace everything else
        message = message.replace("\n", "<br />")

        # Introduce unicode emoji
        message = emoji.emojize(message, use_aliases=True)

        # Adding <pre> tag for preformated code
        message = re.sub(r"```(.*?)```",r'<pre style="background-color: #E6E5DF; white-space: pre-wrap;">\1</pre>', message)

        return message

    def _slack_to_accepted_emoji(self, message):
        # https://github.com/Ranks/emojione/issues/114
        message = message.replace(":simple_smile:", ":slightly_smiling_face:")
        return message

    def _sub_mention(self, matchobj):
        try:
            return "@{}".format(
                self.__USER_DATA[matchobj.group(0)[2:-1]]["name"]
            )
        except KeyError:
            # In case this identifier is not in __USER_DATA, we fallback to identifier
                return matchobj.group(0)[2:-1]

    def _sub_annotated_mention(self, matchobj):
        return "@{}".format((matchobj.group(0)[2:-1]).split("|")[1])

    def _sub_hyperlink(self, matchobj):
        compound = matchobj.group(0)[1:-1]
        if len(compound.split("|")) == 2:
            url, title = compound.split("|")
        else:
            url, title = compound, compound
        result = "[{title}]({url})".format(url=url, title=title)
        return result

    def _sub_hashtag(self, matchobj):
        text = matchobj.group(0)

        starting_space = " " if text[0] == " " else ""
        ending_space = " " if text[-1] == " " else ""

        return "{}*{}*{}".format(
            starting_space,
            text.strip(),
            ending_space
        )

    def _sub_channel_ref(self, matchobj):
        channel_id = matchobj.group(0)[2:-1]
        try:
            channel_name = self.__CHANNEL_DATA[channel_id]["name"]
        except KeyError as e:
            logging.error("A channel reference was detected but metadata "
                          "not found in channels.json: {}".format(e))
            channel_name = channel_id
        return "*#{}*".format(channel_name)

    def __em_strong(self, matchobj, format="em"):
        if format not in ("em", "strong"):
            raise ValueError
        chars = "*" if format == "em" else "**"

        text = matchobj.group(0)
        starting_space = " " if text[0] == " " else ""
        ending_space = " " if text[-1] == " " else ""
        return "{}{}{}{}{}".format(
            starting_space,
            chars,
            matchobj.group(0).strip()[1:-1],
            chars,
            ending_space
        )

    def _sub_italics(self, matchobj):
        return self.__em_strong(matchobj, "em")

    def _sub_bold(self, matchobj):
        return self.__em_strong(matchobj, "strong")
