import os
import webbrowser

import click
import flask

from slackviewer.app import app

from slackviewer.app import channel_name
import urllib.request

from slackviewer.archive import \
    extract_archive, \
    get_empty_dm_names, \
    get_users, \
    get_channels, \
    get_groups, \
    get_dms, \
    get_mpims, \
    compile_channels, \
    compile_groups, \
    compile_dms, \
    compile_dm_users, \
    compile_mpims, \
    compile_mpim_users


def envvar(name, default):
    """Create callable environment variable getter

    :param str name: Name of environment variable
    :param default: Default value to return in case it isn't defined
    """
    return lambda: os.environ.get(name, default)


def flag_ennvar(name):
    return os.environ.get(name) == '1'


def configure_app(app, archive, debug):
    app.debug = debug
    if app.debug:
        print("WARNING: DEBUG MODE IS ENABLED!")
    app.config["PROPAGATE_EXCEPTIONS"] = True

    path = extract_archive(archive)

    empty_dms = get_empty_dm_names(path)

    user_data = get_users(path)
    channel_data = get_channels(path)
    group_data = get_groups(path)
    dm_data = get_dms(path)
    mpim_data = get_mpims(path)

    channels = compile_channels(path, user_data, channel_data)
    groups = compile_groups(path, user_data, group_data)
    dms = compile_dms(path, user_data, dm_data)
    dm_users = compile_dm_users(path, user_data, dm_data, empty_dms)
    mpims = compile_mpims(path, user_data, dm_data)
    mpim_users = compile_mpim_users(path, user_data, mpim_data)

    top = flask._app_ctx_stack
    top.channels = channels
    top.groups = groups
    top.dms = dms
    top.dm_users = dm_users
    top.mpims = mpims
    top.mpim_users = mpim_users


@click.command()
@click.option('-p', '--port', default=envvar('SEV_PORT', '5000'),
              type=click.INT, help="Host port to serve your content on")
@click.option("-z", "--archive", type=click.Path(), required=True,
              default=envvar('SEV_ARCHIVE', ''),
              help="Path to your Slack export archive (.zip file or directory)")
@click.option('-I', '--ip', default=envvar('SEV_IP', 'localhost'),
              type=click.STRING, help="Host IP to serve your content on")
@click.option('--no-browser', is_flag=True,
              default=flag_ennvar("SEV_NO_BROWSER"),
              help="If you do not want a browser to open "
                   "automatically, set this.")
@click.option('--test', is_flag=True, default=flag_ennvar("SEV_TEST"),
              help="Runs in 'test' mode, i.e., this will do an archive extract, but will not start the server,"
                   " and immediately quit.")
@click.option('--debug', is_flag=True, default=flag_ennvar("FLASK_DEBUG"))
def main(port, archive, ip, no_browser, test, debug):
    if not archive:
        raise ValueError("Empty path provided for archive")

    configure_app(app, archive, debug)

    if not no_browser and not test:
        webbrowser.open("http://{}:{}".format(ip, port))

    if not test:
        app.run(
            host=ip,
            port=port
        )
        
        
    #download code
    
    avatar_dir = "avatars"
    if not os.path.exists(avatar_dir):
        os.makedirs(avatar_dir)
    
    users = get_users(extract_archive(archive))
    
    sizes = ["24", "32", "48", "72", "192", "512"]
    for size in sizes:
        if not os.path.exists(os.path.join(avatar_dir, size)):
            os.makedirs(os.path.join(avatar_dir, size))
        
        for user in users:
            url = users[user]["profile"]["image_{}".format(size)]
            if url != "":
                filename, file_extension = os.path.splitext(url)
                file_to_save = os.path.join(avatar_dir, size, "{}_{}{}".format(user, size, file_extension))
                if not os.path.exists(file_to_save):
                    urllib.request.urlretrieve(url, file_to_save)
            print("{} {}".format(size, user))
    
    
    
    name = "thelunchers"
    app1 = flask.Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app1.config["SERVER_NAME"] = "test"
    with app1.app_context():
        with open('out.html', 'w', encoding="utf-8") as file:
            file.write(channel_name(name))
    #for channel in channels:
        #print(channel)