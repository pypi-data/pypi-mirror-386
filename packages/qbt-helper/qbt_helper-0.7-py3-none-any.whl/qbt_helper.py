#!/usr/bin/env python3

"""qbt-helper

Usage:
    qbt-helper (HOSTNAME) (USERNAME) (PASSWORD)
    qbt-helper -h

Examples:
    qbt-helper "http://localhost:8080" "admin" "adminadmin"
    qbt-helper "https://cat.seedhost.eu/lol/qbittorrent" "lol" "meow"

Options:
    -h, --help      show this help message and exit
"""

import json
import os

import qbittorrentapi
import requests
from bs4 import BeautifulSoup
from docopt import docopt
from rich import print
from rich.prompt import Prompt
from rich.tree import Tree


def add_torrents(urls: list[str], conn_info: dict):
    """
    Add torrents from their URLs.

    Params:
        urls: list of strings that are URLs.
        conn_info: dict containing qbittorrent login info
    """
    with qbittorrentapi.Client(**conn_info) as qbt_client:
        for url in urls:
            try:
                qbt_client.torrents_add(url, category="distro")
                print(f"Added {os.path.basename(url)}")
            except Exception as ex:
                print(f"Failed to add torrent: {os.path.basename(url)}")


def get_torrents_from_html(webpage_url: str, torrent_substring: str) -> list:
    """
    Add torrent URLs from an HTML web page.

    Params:
        webpage_url: a string that is the URL for the desired webpage.
        torrent_substring: a string that is a substring of the URLs in
            the webpage that you want to extract. It serves as a
            selector.
    """
    reqs = requests.get(webpage_url, timeout=60)
    soup = BeautifulSoup(reqs.text, "html.parser")
    urls = []
    for link in soup.find_all("a"):
        if torrent_substring in link.get("href"):
            url = f"{webpage_url}/{link.get('href')}"
            response = requests.get(url)
            if response.status_code == 200:
                urls.append(url)
            else:
                exit(f"Error verifying the URL: {url}")

    return urls


def remove_torrents(distro_substring: str, conn_info: dict):
    """
    Remove torrents by selecting a substring that corresponds to the
    distro's torrent file name. When the substring is found, the
    torrent is removed by passing the corresponding hash to the method.

    Params:
        distro_substring: a string that is a substring of the distro
            torrent's file name.
        conn_info: dict containing qbittorrent login info.
    """
    with qbittorrentapi.Client(**conn_info) as qbt_client:
        for torrent in qbt_client.torrents_info():
            if distro_substring in torrent.name:
                qbt_client.torrents_delete(
                    torrent_hashes=torrent.hash, delete_files=True
                )
                print(f"Removed {torrent.name}")


def get_almalinux_urls(rel_ver: str) -> list:
    """
    Add AlmaLinux torrents from a list of URLs. These URLs are partially
    hardcoded for convenience and aren't expected to change frequently.

    Params:
        relver: the AlmaLinux release version.
    """
    urls = [
        f"https://almalinux-mirror.dal1.hivelocity.net/{rel_ver}/isos/aarch64/AlmaLinux-{rel_ver}-aarch64.torrent",
        f"https://almalinux-mirror.dal1.hivelocity.net/{rel_ver}/isos/ppc64le/AlmaLinux-{rel_ver}-ppc64le.torrent",
        f"https://almalinux-mirror.dal1.hivelocity.net/{rel_ver}/isos/s390x/AlmaLinux-{rel_ver}-s390x.torrent",
        f"https://almalinux-mirror.dal1.hivelocity.net/{rel_ver}/isos/x86_64/AlmaLinux-{rel_ver}-x86_64.torrent",
    ]

    return urls


def get_antix_urls(rel_ver: str) -> list:
    """
    Add antiX URLs.

    Params:
        relver: the antiX release version.
    """
    urls = [
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}_386-base.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}_386-core.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}_386-full.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-x64-base.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-x64-core.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-x64-full.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-net_386-net.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-net_x64-net.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit_386-base.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit_386-core.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit_386-full.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit_x64-base.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit_x64-core.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit_x64-full.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit-net_386-net.iso.torrent",
        f"https://l2.mxrepo.com/torrents/antiX-{rel_ver}-runit-net_x64-net.iso.torrent",
    ]

    return urls


def get_debian_urls(rel_ver: str) -> list:
    """
    Add Debian torrents from a list of URLs.

    Params:
        relver: the Debian release version.
    """
    urls = [
        f"https://cdimage.debian.org/debian-cd/current/amd64/bt-dvd/debian-{rel_ver}-amd64-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/arm64/bt-dvd/debian-{rel_ver}-arm64-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/armel/bt-dvd/debian-{rel_ver}-armel-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/armhf/bt-dvd/debian-{rel_ver}-armhf-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/mips64el/bt-dvd/debian-{rel_ver}-mips64el-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/mipsel/bt-dvd/debian-{rel_ver}-mipsel-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/ppc64el/bt-dvd/debian-{rel_ver}-ppc64el-DVD-1.iso.torrent",
        f"https://cdimage.debian.org/debian-cd/current/s390x/bt-dvd/debian-{rel_ver}-s390x-DVD-1.iso.torrent",
    ]

    return urls


def get_devuan_urls(rel_ver: str) -> list:
    """
    Add Devuan torrents from a URL.

    Params:
        relver: the Devuan release version.
    """
    return [f"https://files.devuan.org/devuan_{rel_ver}.torrent"]


def get_fedora_urls(rel_ver: str) -> list:
    """
    Add Fedora torrents from URLs extracted from a webpage.

    Params:
        relver: the Fedora release version.
    """
    webpage_url = "https://torrent.fedoraproject.org/torrents"
    torrent_substring = f"{rel_ver}.torrent"
    return get_torrents_from_html(webpage_url, torrent_substring)


def get_freebsd_urls(rel_ver: str) -> list:
    """
    Add FreeBSD torrents via a text file on the web that contains their
    magnet links.

    Params:
        relver: the FreeBSD release version.
    """
    url = f"https://people.freebsd.org/~jmg/FreeBSD-{rel_ver}-R-magnet.txt"
    reqs = requests.get(url, timeout=60)
    data = reqs.text.split("\n")

    magnet_urls = []
    for line in data:
        if line.startswith("magnet:"):
            magnet_urls.append(line)

    return magnet_urls


def get_kali_urls() -> list:
    """
    Add Kali Linux torrents from their URLs extracted from a webpage.
    This method does not accept any parameters. The latest Kali Linux
    version is automatically selected.

    Params: none
    """
    webpage_url = "https://kali.download/base-images/current"
    torrent_substring = ".torrent"
    return get_torrents_from_html(webpage_url, torrent_substring)


def get_mxlinux_urls(rel_ver: str) -> list:
    """
    Add MX Linux torrents given their release version.

    Params:
        rel_ver: the MX Linux release version.
    """
    urls = [
        f"https://l2.mxrepo.com/torrents/MX-{rel_ver}_386.iso.torrent",
        f"https://l2.mxrepo.com/torrents/MX-{rel_ver}_ahs_x64.iso.torrent",
        f"https://l2.mxrepo.com/torrents/MX-{rel_ver}_fluxbox_386.iso.torrent",
        f"https://l2.mxrepo.com/torrents/MX-{rel_ver}_fluxbox_x64.iso.torrent",
        f"https://l2.mxrepo.com/torrents/MX-{rel_ver}_KDE_x64.iso.torrent",
        f"https://l2.mxrepo.com/torrents/MX-{rel_ver}_x64.iso.torrent",
        f"https://l2.mxrepo.com/torrents/mx{rel_ver}_rpi_respin_arm64.zip.torrent",
    ]

    return urls


def get_netbsd_urls(rel_ver: str) -> list:
    """
    Add NetBSD torrents from their URLs extracted from a webpage.

    Params:
        rel_ver: the NetBSD release version.
    """
    webpage_url = f"https://cdn.netbsd.org/pub/NetBSD/NetBSD-{rel_ver}/images/"
    torrent_substring = ".torrent"
    return get_torrents_from_html(webpage_url, torrent_substring)


def get_nixos_urls() -> list:
    """
    Add NixOS torrents from their GitHub release at
    https://github.com/AninMouse/NixOS-ISO-Torrents. This method does not
    accept any paramters. The latest NixOS torrent is automatically selected.

    Params: none
    """
    url = "https://api.github.com/repos/AnimMouse/NixOS-ISO-Torrents/releases/latest"
    reqs = requests.get(url, timeout=60)
    json_data = json.loads(reqs.text)

    urls = []
    for item in json_data["assets"]:
        urls.append(item["browser_download_url"])

    return urls


def get_qubes_urls(rel_ver: str) -> list:
    """
    Add QubesOS torrents from their URLs.

    Params:
        relver: the QubesOS release version.
    """
    return [
        f"https://mirrors.edge.kernel.org/qubes/iso/Qubes-R{rel_ver}-x86_64.torrent"
    ]


def get_rockylinux_urls(rel_ver: str) -> list:
    """
    Add Rocky Linux torrents from their URLs.

    Params:
        relver: the Rocky Linux release version.
    """
    urls = [
        f"https://download.rockylinux.org/pub/rocky/{rel_ver}/isos/aarch64/Rocky-{rel_ver}-aarch64-dvd.torrent",
        f"https://download.rockylinux.org/pub/rocky/{rel_ver}/isos/ppc64le/Rocky-{rel_ver}-ppc64le-dvd.torrent",
        f"https://download.rockylinux.org/pub/rocky/{rel_ver}/isos/s390x/Rocky-{rel_ver}-s390x-dvd.torrent",
        f"https://download.rockylinux.org/pub/rocky/{rel_ver}/isos/x86_64/Rocky-{rel_ver}-x86_64-dvd.torrent",
    ]

    return urls


def get_tails_urls(rel_ver: str):
    """
    Add Tails torrents from their URLs.

    Params:
        relver: the Tails release version.
    """
    urls = [
        f"https://tails.net/torrents/files/tails-amd64-{rel_ver}.img.torrent",
        f"https://tails.net/torrents/files/tails-amd64-{rel_ver}.iso.torrent",
    ]

    return urls


def selection_prompt(distro_selection: str) -> tuple:
    choice = Prompt.ask("Enter 'a' to add; 'r' to remove.")
    if distro_selection != "Kali Linux" and distro_selection != "NixOS":
        rel_ver = Prompt.ask(f"Enter a release version for {distro_selection}")
    else:
        rel_ver = None
    return (choice, rel_ver)


def main():
    args = docopt(__doc__)

    conn_info = dict(
        host=args["HOSTNAME"],
        username=args["USERNAME"],
        password=args["PASSWORD"],
    )

    try:
        with qbittorrentapi.Client(**conn_info) as qbt_client:
            qbt_client.auth_log_in()
    except qbittorrentapi.LoginFailed:
        exit("Login failed. Please verify the credentials are correct.")

    distros = [
        "AlmaLinux",
        "antiX",
        "Debian",
        "Devuan",
        "Fedora",
        "FreeBSD",
        "Kali Linux",
        "MX Linux",
        "NetBSD",
        "NixOS",
        "Qubes",
        "Rocky Linux",
        "Tails",
    ]

    distro_tree = Tree("[bold magenta]Available distros[/bold magenta]")
    for distro in distros:
        distro_tree.add(distro)

    print(distro_tree)

    try:
        distro_selection = Prompt.ask("Enter a distro")
        if distro_selection not in distros:
            exit(f"{distro_selection} is not available to this program.")

        action = selection_prompt(distro_selection)

        match distro_selection:
            case "AlmaLinux":
                match action[0]:
                    case "a":
                        add_torrents(get_almalinux_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"AlmaLinux-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "antiX":
                match action[0]:
                    case "a":
                        add_torrents(get_antix_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"antiX-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Debian":
                match action[0]:
                    case "a":
                        add_torrents(get_debian_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"debian-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Devuan":
                match action[0]:
                    case "a":
                        add_torrents(get_devuan_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"devuan_{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Fedora":
                match action[0]:
                    case "a":
                        add_torrents(get_fedora_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents("Fedora", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "FreeBSD":
                match action[0]:
                    case "a":
                        add_torrents(get_freebsd_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"FreeBSD-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Kali Linux":
                match action[0]:
                    case "a":
                        add_torrents(get_kali_urls(), conn_info)
                    case "r":
                        remove_torrents("kali-linux", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "MX Linux":
                match action[0]:
                    case "a":
                        add_torrents(get_mxlinux_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"MX-{action[1]}", conn_info)
                        remove_torrents(f"mx{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "NetBSD":
                match action[0]:
                    case "a":
                        add_torrents(get_netbsd_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"NetBSD-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "NixOS":
                match action[0]:
                    case "a":
                        add_torrents(get_nixos_urls(), conn_info)
                    case "r":
                        remove_torrents("nixos", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Qubes":
                match action[0]:
                    case "a":
                        add_torrents(get_qubes_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"Qubes-R{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Rocky Linux":
                match action[0]:
                    case "a":
                        add_torrents(get_rockylinux_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"Rocky-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case "Tails":
                match action[0]:
                    case "a":
                        add_torrents(get_tails_urls(action[1]), conn_info)
                    case "r":
                        remove_torrents(f"tails-amd64-{action[1]}", conn_info)
                    case _:
                        exit("Invalid action choice.")

            case _:
                exit("Invalid distro choice.")
    except KeyboardInterrupt:
        exit("Keyboard interrupt detected. Exiting.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit("Keyboard interrupt detected. Exiting.")
