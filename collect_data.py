"""
ARAB HERITAGE COLLECTOR - ORGANIZED BY COUNTRY FOR RAG
======================================================
Perfect for RAG systems - each country gets ONE comprehensive file
When you search "Jordan", you get ALL Jordan info in one place!

Install: pip install wikipedia-api requests beautifulsoup4 --break-system-packages
Usage: python3 arab_heritage_rag_collector.py
"""

import wikipediaapi
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os


class HeritageCollector:
    """Collects heritage site information"""

    def __init__(self, site_name, site_type, country, era=None):
        self.site_name = site_name
        self.site_type = site_type
        self.country = country
        self.era = era
        self.data = {
            'site_name': site_name,
            'type': site_type,
            'country': country,
            'historical_era': era,
            'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sources': []
        }

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def collect_wikipedia(self, languages=['en', 'ar', 'fr']):
        """Collect from Wikipedia in multiple languages"""
        for lang in languages:
            try:
                wiki = wikipediaapi.Wikipedia(
                    language=lang,
                    user_agent='ArabHeritageRAG/1.0'
                )

                page = wiki.page(self.site_name)

                if page.exists():
                    self.data['sources'].append({
                        'source': f'Wikipedia-{lang.upper()}',
                        'language': lang,
                        'url': page.fullurl,
                        'title': page.title,
                        'content': page.text,
                        'summary': page.summary,
                        'word_count': len(page.text.split())
                    })

                time.sleep(1)

            except Exception:
                pass

    def collect_wikivoyage(self):
        """Collect from Wikivoyage"""
        url = f"https://en.wikivoyage.org/wiki/{self.site_name.replace(' ', '_')}"

        try:
            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                content_div = soup.find('div', {'id': 'mw-content-text'})

                if content_div:
                    for unwanted in content_div.find_all(['script', 'style', 'table', 'nav']):
                        unwanted.decompose()

                    sections = {}
                    current_section = 'Overview'
                    sections[current_section] = []

                    for element in content_div.find_all(['h2', 'h3', 'p', 'ul']):
                        if element.name in ['h2', 'h3']:
                            current_section = element.get_text().strip()
                            sections[current_section] = []
                        elif element.name == 'p':
                            text = element.get_text().strip()
                            if len(text) > 50:
                                sections[current_section].append(text)
                        elif element.name == 'ul':
                            items = [li.get_text().strip() for li in element.find_all('li')]
                            sections[current_section].extend(items)

                    full_content = "\n\n".join([
                        f"## {section}\n" + "\n".join(texts)
                        for section, texts in sections.items() if texts
                    ])

                    if full_content:
                        self.data['sources'].append({
                            'source': 'Wikivoyage',
                            'language': 'en',
                            'url': url,
                            'content': full_content,
                            'word_count': len(full_content.split())
                        })

        except Exception:
            pass

        time.sleep(1)

    def collect_all(self):
        """Run all collectors"""
        self.collect_wikipedia()
        self.collect_wikivoyage()
        return self.data

    def get_stats(self):
        """Return collection statistics"""
        if not self.data['sources']:
            return 0, 0
        total_words = sum(s['word_count'] for s in self.data['sources'])
        return len(self.data['sources']), total_words


class CountryDatabase:
    """Manages country-organized database for RAG"""

    def __init__(self, output_dir='arab_heritage_by_country'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def add_site(self, site_data):
        """Add site to country database"""
        country = site_data['country']
        country_safe = country.lower().replace(' ', '_')
        country_dir = os.path.join(self.output_dir, country_safe)
        os.makedirs(country_dir, exist_ok=True)

        # Save individual site JSON
        site_safe = site_data['site_name'].lower().replace(' ', '_').replace('/', '_')
        individual_json = f"{country_dir}/{site_safe}.json"
        with open(individual_json, 'w', encoding='utf-8') as f:
            json.dump(site_data, f, indent=2, ensure_ascii=False)

        # APPEND to master country TXT (PERFECT FOR RAG!)
        master_txt = f"{country_dir}/_COMPLETE_{country_safe}.txt"
        with open(master_txt, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'=' * 100}\n")
            f.write(f"{'=' * 100}\n")
            f.write(f"{site_data['site_name'].upper()}\n")
            f.write(f"{'=' * 100}\n")
            f.write(f"{'=' * 100}\n\n")
            f.write(f"Country: {site_data['country']}\n")
            f.write(f"Type: {site_data['type']}\n")
            f.write(f"Historical Era: {site_data['historical_era'] or 'Various'}\n")
            f.write(f"Collected: {site_data['collected_date']}\n\n")

            for source in site_data['sources']:
                f.write(f"\n{'-' * 100}\n")
                f.write(f"SOURCE: {source['source']} ({source['language']}) | Words: {source['word_count']:,}\n")
                f.write(f"URL: {source['url']}\n")
                f.write(f"{'-' * 100}\n\n")
                f.write(source['content'])
                f.write("\n\n")

        # APPEND to master country JSON (structured for RAG metadata)
        master_json = f"{country_dir}/_COMPLETE_{country_safe}.json"
        if os.path.exists(master_json):
            with open(master_json, 'r', encoding='utf-8') as f:
                country_data = json.load(f)
        else:
            country_data = {
                'country': country,
                'total_sites': 0,
                'total_words': 0,
                'last_updated': '',
                'sites': []
            }

        country_data['sites'].append(site_data)
        country_data['total_sites'] = len(country_data['sites'])
        country_data['total_words'] = sum(
            sum(s['word_count'] for s in site['sources'])
            for site in country_data['sites']
        )
        country_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(master_json, 'w', encoding='utf-8') as f:
            json.dump(country_data, f, indent=2, ensure_ascii=False)

        return master_txt, master_json


# ==================== COMPLETE SITE DATABASE ====================

ALL_SITES = [
    # 🇵🇸 PALESTINE (46 sites)
    {'name': 'Jerusalem', 'type': 'ancient_city', 'country': 'Palestine'},
    {'name': 'Hebron', 'type': 'ancient_city', 'country': 'Palestine'},
    {'name': 'Bethlehem', 'type': 'ancient_city', 'country': 'Palestine'},
    {'name': 'Jericho', 'type': 'ancient_city', 'country': 'Palestine'},
    {'name': 'Nablus', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Gaza City', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Ramallah', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Jenin', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Tulkarm', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Qalqilya', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Khan Yunis', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Rafah', 'type': 'city', 'country': 'Palestine'},
    {'name': 'Beit Jala', 'type': 'town', 'country': 'Palestine'},
    {'name': 'Beit Sahour', 'type': 'town', 'country': 'Palestine'},
    {'name': 'Sebastia', 'type': 'ancient_village', 'country': 'Palestine'},
    {'name': 'Battir', 'type': 'ancient_village', 'country': 'Palestine'},
    {'name': 'Taybeh', 'type': 'village', 'country': 'Palestine'},
    {'name': 'Artas', 'type': 'village', 'country': 'Palestine'},
    {'name': 'Burqin', 'type': 'village', 'country': 'Palestine'},
    {'name': 'Al-Aqsa Mosque', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Dome of the Rock', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Church of the Holy Sepulchre', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Western Wall', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Mount of Olives', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Tomb of the Patriarchs', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Church of the Nativity', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Mar Saba Monastery', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'St. George Monastery', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Hisham Palace', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Tel es-Sultan', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Mount Gerizim', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Jacobs Well', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Solomon Pools', 'type': 'historical_site', 'country': 'Palestine'},
    {'name': 'Herodium', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Qumran Caves', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Saint Hilarion Monastery', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Khan al-Umdan', 'type': 'historical_site', 'country': 'Palestine'},
    {'name': 'Great Omari Mosque', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Church of Saint Porphyrius', 'type': 'religious_site', 'country': 'Palestine'},
    {'name': 'Tell es-Safi (Gath)', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Samaria (Sebaste)', 'type': 'ancient_city', 'country': 'Palestine'},
    {'name': 'Khirbet al-Mafjar', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Tell Balata (Shechem)', 'type': 'archaeological_site', 'country': 'Palestine'},
    {'name': 'Silwan', 'type': 'ancient_village', 'country': 'Palestine'},
    {'name': 'Lifta', 'type': 'abandoned_village', 'country': 'Palestine'},
    {'name': 'Ein Kerem', 'type': 'village', 'country': 'Palestine'},

    # 🇪🇬 EGYPT (63 sites)
    {'name': 'Cairo', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Alexandria', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Luxor', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Aswan', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Giza', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Faiyum', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Minya', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Port Said', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Marsa Matruh', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Ismailia', 'type': 'city', 'country': 'Egypt'},
    {'name': 'Siwa Oasis', 'type': 'oasis', 'country': 'Egypt'},
    {'name': 'Bahariya Oasis', 'type': 'oasis', 'country': 'Egypt'},
    {'name': 'Farafra Oasis', 'type': 'oasis', 'country': 'Egypt'},
    {'name': 'Dakhla Oasis', 'type': 'oasis', 'country': 'Egypt'},
    {'name': 'Kharga Oasis', 'type': 'oasis', 'country': 'Egypt'},
    {'name': 'Sharm El Sheikh', 'type': 'resort_town', 'country': 'Egypt'},
    {'name': 'Dahab', 'type': 'resort_town', 'country': 'Egypt'},
    {'name': 'Hurghada', 'type': 'resort_town', 'country': 'Egypt'},
    {'name': 'Marsa Alam', 'type': 'resort_town', 'country': 'Egypt'},
    {'name': 'Pyramids of Giza', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Great Sphinx of Giza', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Saqqara Necropolis', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Pyramid of Djoser', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Dahshur', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Memphis Egypt', 'type': 'ancient_city', 'country': 'Egypt'},
    {'name': 'Valley of the Kings', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Valley of the Queens', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Karnak Temple Complex', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Luxor Temple', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Deir el-Bahari', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Ramesseum', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Medinet Habu', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Colossi of Memnon', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Temple of Edfu', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Temple of Kom Ombo', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Philae Temple', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Abu Simbel Temples', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Dendera Temple complex', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Abydos', 'type': 'ancient_city', 'country': 'Egypt'},
    {'name': 'Temple of Seti I', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Saint Catherines Monastery', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Mount Sinai', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Al-Azhar Mosque', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Mosque of Ibn Tulun', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Sultan Hassan Mosque', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Saladin Citadel', 'type': 'fortress', 'country': 'Egypt'},
    {'name': 'Hanging Church', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Ben Ezra Synagogue', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Khan el-Khalili', 'type': 'historical_market', 'country': 'Egypt'},
    {'name': 'City of the Dead Cairo', 'type': 'historical_site', 'country': 'Egypt'},
    {'name': 'Abu Mena', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Amarna', 'type': 'ancient_city', 'country': 'Egypt'},
    {'name': 'Beni Hassan', 'type': 'archaeological_site', 'country': 'Egypt'},
    {'name': 'Wadi al-Hitan (Valley of the Whales)', 'type': 'natural_site', 'country': 'Egypt'},
    {'name': 'White Desert', 'type': 'natural_site', 'country': 'Egypt'},
    {'name': 'Black Desert', 'type': 'natural_site', 'country': 'Egypt'},
    {'name': 'St. Anthony Monastery', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'St. Paul Monastery', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Wadi El Natrun', 'type': 'religious_site', 'country': 'Egypt'},
    {'name': 'Rosetta (Rashid)', 'type': 'historical_city', 'country': 'Egypt'},
    {'name': 'El Alamein', 'type': 'historical_site', 'country': 'Egypt'},
    {'name': 'Tanis', 'type': 'ancient_city', 'country': 'Egypt'},
    {'name': 'Bubastis', 'type': 'ancient_city', 'country': 'Egypt'},

    # 🇯🇴 JORDAN (33 sites)
    {'name': 'Amman', 'type': 'city', 'country': 'Jordan'},
    {'name': 'Aqaba', 'type': 'city', 'country': 'Jordan'},
    {'name': 'Petra', 'type': 'ancient_city', 'country': 'Jordan'},
    {'name': 'Little Petra', 'type': 'archaeological_site', 'country': 'Jordan'},
    {'name': 'Jerash', 'type': 'ancient_city', 'country': 'Jordan'},
    {'name': 'Umm Qais', 'type': 'ancient_city', 'country': 'Jordan'},
    {'name': 'Pella Jordan', 'type': 'ancient_city', 'country': 'Jordan'},
    {'name': 'Umm al-Jimal', 'type': 'ancient_city', 'country': 'Jordan'},
    {'name': 'Madaba', 'type': 'city', 'country': 'Jordan'},
    {'name': 'Mount Nebo', 'type': 'religious_site', 'country': 'Jordan'},
    {'name': 'Bethany Beyond the Jordan', 'type': 'religious_site', 'country': 'Jordan'},
    {'name': 'Wadi Rum', 'type': 'natural_site', 'country': 'Jordan'},
    {'name': 'Dead Sea', 'type': 'natural_site', 'country': 'Jordan'},
    {'name': 'Kerak Castle', 'type': 'fortress', 'country': 'Jordan'},
    {'name': 'Ajloun Castle', 'type': 'fortress', 'country': 'Jordan'},
    {'name': 'Shobak Castle', 'type': 'fortress', 'country': 'Jordan'},
    {'name': 'Quseir Amra', 'type': 'desert_castle', 'country': 'Jordan'},
    {'name': 'Qasr Kharana', 'type': 'desert_castle', 'country': 'Jordan'},
    {'name': 'Qasr Azraq', 'type': 'desert_castle', 'country': 'Jordan'},
    {'name': 'Amman Citadel', 'type': 'archaeological_site', 'country': 'Jordan'},
    {'name': 'Roman Theater Amman', 'type': 'archaeological_site', 'country': 'Jordan'},
    {'name': 'Dana Biosphere Reserve', 'type': 'natural_site', 'country': 'Jordan'},
    {'name': 'Wadi Mujib', 'type': 'natural_site', 'country': 'Jordan'},
    {'name': 'Iraq al-Amir', 'type': 'archaeological_site', 'country': 'Jordan'},
    {'name': 'Mukawir (Machaerus)', 'type': 'archaeological_site', 'country': 'Jordan'},
    {'name': 'Umm ar-Rasas', 'type': 'archaeological_site', 'country': 'Jordan'},
    {'name': 'Tell Mar Elias', 'type': 'religious_site', 'country': 'Jordan'},
    {'name': 'Lot\'s Cave', 'type': 'religious_site', 'country': 'Jordan'},
    {'name': 'Azraq Wetland Reserve', 'type': 'natural_site', 'country': 'Jordan'},
    {'name': 'Fuheis', 'type': 'town', 'country': 'Jordan'},
    {'name': 'Salt', 'type': 'historical_city', 'country': 'Jordan'},
    {'name': 'Ajloun Nature Reserve', 'type': 'natural_site', 'country': 'Jordan'},

    # 🇱🇧 LEBANON (32 sites)
    {'name': 'Beirut', 'type': 'city', 'country': 'Lebanon'},
    {'name': 'Baalbek', 'type': 'ancient_city', 'country': 'Lebanon'},
    {'name': 'Temple of Bacchus', 'type': 'archaeological_site', 'country': 'Lebanon'},
    {'name': 'Temple of Jupiter', 'type': 'archaeological_site', 'country': 'Lebanon'},
    {'name': 'Byblos', 'type': 'ancient_city', 'country': 'Lebanon'},
    {'name': 'Tyre', 'type': 'ancient_city', 'country': 'Lebanon'},
    {'name': 'Sidon', 'type': 'ancient_city', 'country': 'Lebanon'},
    {'name': 'Anjar', 'type': 'ancient_city', 'country': 'Lebanon'},
    {'name': 'Tripoli Lebanon', 'type': 'city', 'country': 'Lebanon'},
    {'name': 'Citadel of Raymond de Saint-Gilles', 'type': 'fortress', 'country': 'Lebanon'},
    {'name': 'Sidon Sea Castle', 'type': 'fortress', 'country': 'Lebanon'},
    {'name': 'Beiteddine Palace', 'type': 'historical_palace', 'country': 'Lebanon'},
    {'name': 'Moussa Castle', 'type': 'museum', 'country': 'Lebanon'},
    {'name': 'Jeita Grotto', 'type': 'natural_site', 'country': 'Lebanon'},
    {'name': 'Qadisha Valley', 'type': 'natural_site', 'country': 'Lebanon'},
    {'name': 'Cedars of God', 'type': 'natural_site', 'country': 'Lebanon'},
    {'name': 'Beaufort Castle', 'type': 'fortress', 'country': 'Lebanon'},
    {'name': 'Mseilha Fort', 'type': 'fortress', 'country': 'Lebanon'},
    {'name': 'Temple of Eshmun', 'type': 'archaeological_site', 'country': 'Lebanon'},
    {'name': 'Deir el Qamar', 'type': 'historical_village', 'country': 'Lebanon'},
    {'name': 'Zahle', 'type': 'city', 'country': 'Lebanon'},
    {'name': 'Batroun', 'type': 'town', 'country': 'Lebanon'},
    {'name': 'Bcharre', 'type': 'town', 'country': 'Lebanon'},
    {'name': 'Ammiq Wetland', 'type': 'natural_site', 'country': 'Lebanon'},
    {'name': 'Palm Islands Nature Reserve', 'type': 'natural_site', 'country': 'Lebanon'},
    {'name': 'Tannourine', 'type': 'town', 'country': 'Lebanon'},
    {'name': 'Ehden', 'type': 'town', 'country': 'Lebanon'},
    {'name': 'Zgharta', 'type': 'town', 'country': 'Lebanon'},
    {'name': 'Jabal Moussa Biosphere Reserve', 'type': 'natural_site', 'country': 'Lebanon'},
    {'name': 'Tyre Beach', 'type': 'natural_site', 'country': 'Lebanon'},

    # 🇸🇾 SYRIA (32 sites)
    {'name': 'Damascus', 'type': 'city', 'country': 'Syria'},
    {'name': 'Ancient City of Damascus', 'type': 'ancient_city', 'country': 'Syria'},
    {'name': 'Umayyad Mosque', 'type': 'religious_site', 'country': 'Syria'},
    {'name': 'Aleppo', 'type': 'city', 'country': 'Syria'},
    {'name': 'Citadel of Aleppo', 'type': 'fortress', 'country': 'Syria'},
    {'name': 'Great Mosque of Aleppo', 'type': 'religious_site', 'country': 'Syria'},
    {'name': 'Palmyra', 'type': 'ancient_city', 'country': 'Syria'},
    {'name': 'Temple of Bel', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Bosra', 'type': 'ancient_city', 'country': 'Syria'},
    {'name': 'Bosra Amphitheater', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Krak des Chevaliers', 'type': 'fortress', 'country': 'Syria'},
    {'name': 'Citadel of Saladin', 'type': 'fortress', 'country': 'Syria'},
    {'name': 'Norias of Hama', 'type': 'historical_site', 'country': 'Syria'},
    {'name': 'Apamea', 'type': 'ancient_city', 'country': 'Syria'},
    {'name': 'Ebla', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Mari Syria', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Ugarit', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Dead Cities', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Church of Saint Simeon Stylites', 'type': 'religious_site', 'country': 'Syria'},
    {'name': 'Maaloula', 'type': 'ancient_village', 'country': 'Syria'},
    {'name': 'Sednaya', 'type': 'ancient_village', 'country': 'Syria'},
    {'name': 'Amrit', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Arwad', 'type': 'island', 'country': 'Syria'},
    {'name': 'Rasafa (Sergiopolis)', 'type': 'ancient_city', 'country': 'Syria'},
    {'name': 'Qasr al-Hayr al-Sharqi', 'type': 'desert_castle', 'country': 'Syria'},
    {'name': 'Qasr al-Hayr al-Gharbi', 'type': 'desert_castle', 'country': 'Syria'},
    {'name': 'Tell Brak', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Tell Halaf', 'type': 'archaeological_site', 'country': 'Syria'},
    {'name': 'Salkhad', 'type': 'historical_town', 'country': 'Syria'},
    {'name': 'Safita', 'type': 'town', 'country': 'Syria'},
    {'name': 'Masyaf', 'type': 'town', 'country': 'Syria'},
    {'name': 'Wadi al-Nasara', 'type': 'region', 'country': 'Syria'},

    # 🇮🇶 IRAQ (38 sites)
    {'name': 'Baghdad', 'type': 'city', 'country': 'Iraq'},
    {'name': 'Al-Mutanabbi Street', 'type': 'historical_site', 'country': 'Iraq'},
    {'name': 'Abbasid Palace', 'type': 'historical_site', 'country': 'Iraq'},
    {'name': 'Al-Mustansiriya Madrasah', 'type': 'historical_site', 'country': 'Iraq'},
    {'name': 'Babylon', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Ishtar Gate', 'type': 'archaeological_site', 'country': 'Iraq'},
    {'name': 'Hanging Gardens of Babylon', 'type': 'legendary_site', 'country': 'Iraq'},
    {'name': 'Ur', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Great Ziggurat of Ur', 'type': 'archaeological_site', 'country': 'Iraq'},
    {'name': 'Uruk', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Nippur', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Hatra', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Ashur', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Nimrud', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Nineveh', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Samarra', 'type': 'city', 'country': 'Iraq'},
    {'name': 'Great Mosque of Samarra', 'type': 'historical_site', 'country': 'Iraq'},
    {'name': 'Malwiya Minaret', 'type': 'historical_site', 'country': 'Iraq'},
    {'name': 'Ctesiphon', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Taq Kasra', 'type': 'archaeological_site', 'country': 'Iraq'},
    {'name': 'Najaf', 'type': 'city', 'country': 'Iraq'},
    {'name': 'Imam Ali Shrine', 'type': 'religious_site', 'country': 'Iraq'},
    {'name': 'Karbala', 'type': 'city', 'country': 'Iraq'},
    {'name': 'Imam Hussein Shrine', 'type': 'religious_site', 'country': 'Iraq'},
    {'name': 'Erbil Citadel', 'type': 'fortress', 'country': 'Iraq'},
    {'name': 'Shanidar Cave', 'type': 'archaeological_site', 'country': 'Iraq'},
    {'name': 'Ziggurat of Dur-Kurigalzu', 'type': 'archaeological_site', 'country': 'Iraq'},
    {'name': 'Al-Ukhaidir Fortress', 'type': 'fortress', 'country': 'Iraq'},
    {'name': 'Dur-Kurigalzu', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Sippar', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Shuruppak', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Girsu', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Larsa', 'type': 'ancient_city', 'country': 'Iraq'},
    {'name': 'Eridu', 'type': 'ancient_city', 'country': 'Iraq'},

    # 🇸🇦 SAUDI ARABIA (34 sites)
    {'name': 'Mada\'in Saleh', 'type': 'ancient_city', 'country': 'Saudi Arabia'},
    {'name': 'Hegra', 'type': 'archaeological_site', 'country': 'Saudi Arabia'},
    {'name': 'AlUla', 'type': 'historical_region', 'country': 'Saudi Arabia'},
    {'name': 'Dedan', 'type': 'ancient_city', 'country': 'Saudi Arabia'},
    {'name': 'Jabal Ikmah', 'type': 'archaeological_site', 'country': 'Saudi Arabia'},
    {'name': 'Elephant Rock', 'type': 'natural_site', 'country': 'Saudi Arabia'},
    {'name': 'Diriyah', 'type': 'historical_city', 'country': 'Saudi Arabia'},
    {'name': 'At-Turaif District', 'type': 'historical_site', 'country': 'Saudi Arabia'},
    {'name': 'Al-Balad, Jeddah', 'type': 'historical_district', 'country': 'Saudi Arabia'},
    {'name': 'Nasseef House', 'type': 'historical_building', 'country': 'Saudi Arabia'},
    {'name': 'Rock Art in the Hail Region', 'type': 'archaeological_site', 'country': 'Saudi Arabia'},
    {'name': 'Jubbah', 'type': 'archaeological_site', 'country': 'Saudi Arabia'},
    {'name': 'Al-Ahsa Oasis', 'type': 'natural_site', 'country': 'Saudi Arabia'},
    {'name': 'Ibrahim Palace', 'type': 'historical_site', 'country': 'Saudi Arabia'},
    {'name': 'Rijal Almaa', 'type': 'historical_village', 'country': 'Saudi Arabia'},
    {'name': 'Masmak Fortress', 'type': 'fortress', 'country': 'Saudi Arabia'},
    {'name': 'Murabba Palace', 'type': 'historical_palace', 'country': 'Saudi Arabia'},
    {'name': 'Al Fao', 'type': 'ancient_city', 'country': 'Saudi Arabia'},
    {'name': 'Dhee Ayn', 'type': 'historical_village', 'country': 'Saudi Arabia'},
    {'name': 'Ushaiger Heritage Village', 'type': 'historical_village', 'country': 'Saudi Arabia'},
    {'name': 'Domat al-Jandal', 'type': 'historical_site', 'country': 'Saudi Arabia'},
    {'name': 'Marid Castle', 'type': 'fortress', 'country': 'Saudi Arabia'},
    {'name': 'Edge of the World', 'type': 'natural_site', 'country': 'Saudi Arabia'},
    {'name': 'Farasan Islands', 'type': 'natural_site', 'country': 'Saudi Arabia'},
    {'name': 'Al-Wahba Crater', 'type': 'natural_site', 'country': 'Saudi Arabia'},
    {'name': 'Al-Nafud Desert', 'type': 'natural_site', 'country': 'Saudi Arabia'},

    # 🇾🇪 YEMEN (29 sites)
    {'name': 'Old City of Sanaa', 'type': 'ancient_city', 'country': 'Yemen'},
    {'name': 'Great Mosque of Sanaa', 'type': 'religious_site', 'country': 'Yemen'},
    {'name': 'Dar al-Hajar', 'type': 'historical_palace', 'country': 'Yemen'},
    {'name': 'Shibam', 'type': 'ancient_city', 'country': 'Yemen'},
    {'name': 'Zabid', 'type': 'ancient_city', 'country': 'Yemen'},
    {'name': 'Aden', 'type': 'city', 'country': 'Yemen'},
    {'name': 'Cisterns of Tawila', 'type': 'historical_site', 'country': 'Yemen'},
    {'name': 'Sira Fortress', 'type': 'fortress', 'country': 'Yemen'},
    {'name': 'Marib Dam', 'type': 'ancient_site', 'country': 'Yemen'},
    {'name': 'Throne of Bilqis', 'type': 'archaeological_site', 'country': 'Yemen'},
    {'name': 'Temple of Awwam', 'type': 'archaeological_site', 'country': 'Yemen'},
    {'name': 'Baraqish', 'type': 'ancient_city', 'country': 'Yemen'},
    {'name': 'Socotra', 'type': 'natural_site', 'country': 'Yemen'},
    {'name': 'Dragon Blood Tree', 'type': 'natural_site', 'country': 'Yemen'},
    {'name': 'Thula', 'type': 'historical_village', 'country': 'Yemen'},
    {'name': 'Taiz', 'type': 'city', 'country': 'Yemen'},
    {'name': 'Al-Qahira Castle', 'type': 'fortress', 'country': 'Yemen'},
    {'name': 'Ashrafiya Mosque', 'type': 'religious_site', 'country': 'Yemen'},
    {'name': 'Jibla', 'type': 'historical_town', 'country': 'Yemen'},
    {'name': 'Al-Mahwit', 'type': 'city', 'country': 'Yemen'},
    {'name': 'Al-Mukalla', 'type': 'city', 'country': 'Yemen'},
    {'name': 'Seiyun', 'type': 'city', 'country': 'Yemen'},
    {'name': 'Tarim', 'type': 'city', 'country': 'Yemen'},
    {'name': 'Wadi Hadhramaut', 'type': 'natural_site', 'country': 'Yemen'},

    # 🇲🇦 MOROCCO (39 sites)
    {'name': 'Medina of Fez', 'type': 'historical_district', 'country': 'Morocco'},
    {'name': 'Al Quaraouiyine', 'type': 'university', 'country': 'Morocco'},
    {'name': 'Medina of Marrakesh', 'type': 'historical_district', 'country': 'Morocco'},
    {'name': 'Jemaa el-Fnaa', 'type': 'cultural_site', 'country': 'Morocco'},
    {'name': 'Koutoubia Mosque', 'type': 'religious_site', 'country': 'Morocco'},
    {'name': 'Bahia Palace', 'type': 'historical_palace', 'country': 'Morocco'},
    {'name': 'El Badi Palace', 'type': 'historical_palace', 'country': 'Morocco'},
    {'name': 'Saadian Tombs', 'type': 'historical_site', 'country': 'Morocco'},
    {'name': 'Ait Benhaddou', 'type': 'ksar', 'country': 'Morocco'},
    {'name': 'Ouarzazate', 'type': 'city', 'country': 'Morocco'},
    {'name': 'Volubilis', 'type': 'ancient_city', 'country': 'Morocco'},
    {'name': 'Meknes', 'type': 'city', 'country': 'Morocco'},
    {'name': 'Bab Mansour', 'type': 'historical_gate', 'country': 'Morocco'},
    {'name': 'Moulay Ismail Mausoleum', 'type': 'religious_site', 'country': 'Morocco'},
    {'name': 'Medina of Tetouan', 'type': 'historical_district', 'country': 'Morocco'},
    {'name': 'Chefchaouen', 'type': 'city', 'country': 'Morocco'},
    {'name': 'Essaouira', 'type': 'city', 'country': 'Morocco'},
    {'name': 'Mazagan', 'type': 'fortress', 'country': 'Morocco'},
    {'name': 'Rabat', 'type': 'city', 'country': 'Morocco'},
    {'name': 'Hassan Tower', 'type': 'historical_site', 'country': 'Morocco'},
    {'name': 'Chellah', 'type': 'archaeological_site', 'country': 'Morocco'},
    {'name': 'Kasbah of the Udayas', 'type': 'fortress', 'country': 'Morocco'},
    {'name': 'Lixus', 'type': 'ancient_city', 'country': 'Morocco'},
    {'name': 'Tin Mal Mosque', 'type': 'religious_site', 'country': 'Morocco'},
    {'name': 'Todra Gorge', 'type': 'natural_site', 'country': 'Morocco'},
    {'name': 'Moulay Idriss Zerhoun', 'type': 'religious_site', 'country': 'Morocco'},
    {'name': 'Ifrane', 'type': 'town', 'country': 'Morocco'},
    {'name': 'Azrou', 'type': 'town', 'country': 'Morocco'},
    {'name': 'Midelt', 'type': 'town', 'country': 'Morocco'},
    {'name': 'Erfoud', 'type': 'town', 'country': 'Morocco'},
    {'name': 'Merzouga', 'type': 'village', 'country': 'Morocco'},
    {'name': 'Zagora', 'type': 'town', 'country': 'Morocco'},
    {'name': 'Tafraoute', 'type': 'town', 'country': 'Morocco'},

    # 🇩🇿 ALGERIA (30 sites)
    {'name': 'Casbah of Algiers', 'type': 'historical_district', 'country': 'Algeria'},
    {'name': 'Notre Dame dAfrique', 'type': 'religious_site', 'country': 'Algeria'},
    {'name': 'Timgad', 'type': 'ancient_city', 'country': 'Algeria'},
    {'name': 'Djemila', 'type': 'ancient_city', 'country': 'Algeria'},
    {'name': 'Tipaza', 'type': 'ancient_city', 'country': 'Algeria'},
    {'name': 'Royal Mausoleum of Mauretania', 'type': 'archaeological_site', 'country': 'Algeria'},
    {'name': 'Hippo Regius', 'type': 'ancient_city', 'country': 'Algeria'},
    {'name': 'Basilica of St Augustine', 'type': 'religious_site', 'country': 'Algeria'},
    {'name': 'M\'zab Valley', 'type': 'historical_region', 'country': 'Algeria'},
    {'name': 'Ghardaia', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Beni Hammad Fort', 'type': 'archaeological_site', 'country': 'Algeria'},
    {'name': 'Tassili n\'Ajjer', 'type': 'archaeological_site', 'country': 'Algeria'},
    {'name': 'Santa Cruz Fort', 'type': 'fortress', 'country': 'Algeria'},
    {'name': 'Tlemcen', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Mansourah', 'type': 'historical_site', 'country': 'Algeria'},
    {'name': 'Great Mosque of Tlemcen', 'type': 'religious_site', 'country': 'Algeria'},
    {'name': 'Constantine Algeria', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Sidi M\'Cid Bridge', 'type': 'historical_site', 'country': 'Algeria'},
    {'name': 'Palace of Ahmed Bey', 'type': 'historical_palace', 'country': 'Algeria'},
    {'name': 'El Kala National Park', 'type': 'natural_site', 'country': 'Algeria'},
    {'name': 'Hoggar Mountains', 'type': 'natural_site', 'country': 'Algeria'},
    {'name': 'Beni Isguen', 'type': 'village', 'country': 'Algeria'},
    {'name': 'El Oued', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Biskra', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Bejaia', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Annaba', 'type': 'city', 'country': 'Algeria'},
    {'name': 'Skikda', 'type': 'city', 'country': 'Algeria'},

    # 🇹🇳 TUNISIA (30 sites)
    {'name': 'Carthage', 'type': 'ancient_city', 'country': 'Tunisia'},
    {'name': 'Baths of Antoninus', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Sidi Bou Said', 'type': 'village', 'country': 'Tunisia'},
    {'name': 'Medina of Tunis', 'type': 'historical_district', 'country': 'Tunisia'},
    {'name': 'Zaytuna Mosque', 'type': 'religious_site', 'country': 'Tunisia'},
    {'name': 'Bardo National Museum', 'type': 'museum', 'country': 'Tunisia'},
    {'name': 'El Djem Amphitheatre', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Kairouan', 'type': 'city', 'country': 'Tunisia'},
    {'name': 'Great Mosque of Kairouan', 'type': 'religious_site', 'country': 'Tunisia'},
    {'name': 'Dougga', 'type': 'ancient_city', 'country': 'Tunisia'},
    {'name': 'Bulla Regia', 'type': 'ancient_city', 'country': 'Tunisia'},
    {'name': 'Utica Tunisia', 'type': 'ancient_city', 'country': 'Tunisia'},
    {'name': 'Kerkouane', 'type': 'ancient_city', 'country': 'Tunisia'},
    {'name': 'Sousse', 'type': 'city', 'country': 'Tunisia'},
    {'name': 'Medina of Sousse', 'type': 'historical_district', 'country': 'Tunisia'},
    {'name': 'Ribat of Sousse', 'type': 'fortress', 'country': 'Tunisia'},
    {'name': 'Matmata', 'type': 'village', 'country': 'Tunisia'},
    {'name': 'Chenini', 'type': 'village', 'country': 'Tunisia'},
    {'name': 'Ksar Ghilane', 'type': 'oasis', 'country': 'Tunisia'},
    {'name': 'Ichkeul National Park', 'type': 'natural_site', 'country': 'Tunisia'},
    {'name': 'Zaghouan Aqueduct', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Thuburbo Majus', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Sbeitla', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Haïdra', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Makthar', 'type': 'archaeological_site', 'country': 'Tunisia'},
    {'name': 'Monastir', 'type': 'city', 'country': 'Tunisia'},
    {'name': 'Mahdia', 'type': 'city', 'country': 'Tunisia'},
    {'name': 'Zaghouan', 'type': 'town', 'country': 'Tunisia'},
    {'name': 'Testour', 'type': 'town', 'country': 'Tunisia'},

    # 🇱🇾 LIBYA (23 sites)
    {'name': 'Leptis Magna', 'type': 'ancient_city', 'country': 'Libya'},
    {'name': 'Sabratha', 'type': 'ancient_city', 'country': 'Libya'},
    {'name': 'Cyrene', 'type': 'ancient_city', 'country': 'Libya'},
    {'name': 'Temple of Zeus Cyrene', 'type': 'archaeological_site', 'country': 'Libya'},
    {'name': 'Ghadames', 'type': 'historical_city', 'country': 'Libya'},
    {'name': 'Tadrart Acacus', 'type': 'archaeological_site', 'country': 'Libya'},
    {'name': 'Tripoli Libya', 'type': 'city', 'country': 'Libya'},
    {'name': 'Red Castle Museum', 'type': 'museum', 'country': 'Libya'},
    {'name': 'Arch of Marcus Aurelius', 'type': 'archaeological_site', 'country': 'Libya'},
    {'name': 'Ptolemais', 'type': 'ancient_city', 'country': 'Libya'},
    {'name': 'Apollonia Libya', 'type': 'ancient_city', 'country': 'Libya'},
    {'name': 'Germa', 'type': 'ancient_city', 'country': 'Libya'},
    {'name': 'Jebel Akhdar Libya', 'type': 'natural_site', 'country': 'Libya'},
    {'name': 'Ubari', 'type': 'oasis', 'country': 'Libya'},
    {'name': 'Ghat', 'type': 'town', 'country': 'Libya'},
    {'name': 'Al-Kufra', 'type': 'oasis', 'country': 'Libya'},
    {'name': 'Benghazi', 'type': 'city', 'country': 'Libya'},
    {'name': 'Misrata', 'type': 'city', 'country': 'Libya'},
    {'name': 'Sabha', 'type': 'city', 'country': 'Libya'},
    {'name': 'Tobruk', 'type': 'city', 'country': 'Libya'},
    {'name': 'Derna', 'type': 'city', 'country': 'Libya'},

    # 🇴🇲 OMAN (27 sites)
    {'name': 'Bahla Fort', 'type': 'fortress', 'country': 'Oman'},
    {'name': 'Nizwa Fort', 'type': 'fortress', 'country': 'Oman'},
    {'name': 'Jabrin Castle', 'type': 'fortress', 'country': 'Oman'},
    {'name': 'Rustaq Fort', 'type': 'fortress', 'country': 'Oman'},
    {'name': 'Nakhal Fort', 'type': 'fortress', 'country': 'Oman'},
    {'name': 'Archaeological Sites of Bat, Al-Khutm and Al-Ayn', 'type': 'archaeological_site', 'country': 'Oman'},
    {'name': 'Land of Frankincense', 'type': 'historical_region', 'country': 'Oman'},
    {'name': 'Al-Baleed Archaeological Park', 'type': 'archaeological_site', 'country': 'Oman'},
    {'name': 'Sumhuram', 'type': 'ancient_city', 'country': 'Oman'},
    {'name': 'Ubar', 'type': 'archaeological_site', 'country': 'Oman'},
    {'name': 'Sultan Qaboos Grand Mosque', 'type': 'religious_site', 'country': 'Oman'},
    {'name': 'Royal Opera House Muscat', 'type': 'cultural_site', 'country': 'Oman'},
    {'name': 'Misfat al Abriyeen', 'type': 'historical_village', 'country': 'Oman'},
    {'name': 'Jebel Shams', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Wadi Shab', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Bimmah Sinkhole', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Daymaniyat Islands', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Nizwa', 'type': 'city', 'country': 'Oman'},
    {'name': 'Salalah', 'type': 'city', 'country': 'Oman'},
    {'name': 'Sur', 'type': 'city', 'country': 'Oman'},
    {'name': 'Al Hamra', 'type': 'town', 'country': 'Oman'},
    {'name': 'Wadi Bani Khalid', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Ras al-Jinz', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Jabal Akhdar', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Barr al Hikman', 'type': 'natural_site', 'country': 'Oman'},
    {'name': 'Masirah Island', 'type': 'natural_site', 'country': 'Oman'},

    # 🇦🇪 UAE (24 sites)
    {'name': 'Sheikh Zayed Grand Mosque', 'type': 'religious_site', 'country': 'UAE'},
    {'name': 'Louvre Abu Dhabi', 'type': 'museum', 'country': 'UAE'},
    {'name': 'Qasr Al Hosn', 'type': 'fortress', 'country': 'UAE'},
    {'name': 'Al Ain Oasis', 'type': 'natural_site', 'country': 'UAE'},
    {'name': 'Jebel Hafeet', 'type': 'archaeological_site', 'country': 'UAE'},
    {'name': 'Hili Archaeological Park', 'type': 'archaeological_site', 'country': 'UAE'},
    {'name': 'Al Fahidi Historical Neighbourhood', 'type': 'historical_district', 'country': 'UAE'},
    {'name': 'Dubai Museum', 'type': 'museum', 'country': 'UAE'},
    {'name': 'Al Badiyah Mosque', 'type': 'religious_site', 'country': 'UAE'},
    {'name': 'Fujairah Fort', 'type': 'fortress', 'country': 'UAE'},
    {'name': 'Dhayah Fort', 'type': 'fortress', 'country': 'UAE'},
    {'name': 'Jazirat Al Hamra', 'type': 'ghost_town', 'country': 'UAE'},
    {'name': 'Mleiha Archaeological Centre', 'type': 'archaeological_site', 'country': 'UAE'},
    {'name': 'Sharjah Museum of Islamic Civilization', 'type': 'museum', 'country': 'UAE'},
    {'name': 'Al Ain', 'type': 'city', 'country': 'UAE'},
    {'name': 'Fujairah', 'type': 'city', 'country': 'UAE'},
    {'name': 'Ras al-Khaimah', 'type': 'city', 'country': 'UAE'},
    {'name': 'Jebel Jais', 'type': 'natural_site', 'country': 'UAE'},
    {'name': 'Sir Bani Yas Island', 'type': 'natural_site', 'country': 'UAE'},

    # 🇶🇦 QATAR (18 sites)
    {'name': 'Souq Waqif', 'type': 'historical_market', 'country': 'Qatar'},
    {'name': 'Museum of Islamic Art', 'type': 'museum', 'country': 'Qatar'},
    {'name': 'National Museum of Qatar', 'type': 'museum', 'country': 'Qatar'},
    {'name': 'Al Zubarah', 'type': 'archaeological_site', 'country': 'Qatar'},
    {'name': 'Barzan Towers', 'type': 'historical_site', 'country': 'Qatar'},
    {'name': 'Katara Cultural Village', 'type': 'cultural_site', 'country': 'Qatar'},
    {'name': 'Al Koot Fort', 'type': 'fortress', 'country': 'Qatar'},
    {'name': 'Khor Al Adaid', 'type': 'natural_site', 'country': 'Qatar'},
    {'name': 'Al Wakrah', 'type': 'city', 'country': 'Qatar'},
    {'name': 'Al Khor', 'type': 'city', 'country': 'Qatar'},
    {'name': 'The Pearl-Qatar', 'type': 'modern_development', 'country': 'Qatar'},
    {'name': 'Lusail', 'type': 'modern_city', 'country': 'Qatar'},

    # 🇧🇭 BAHRAIN (20 sites)
    {'name': 'Qal\'at al-Bahrain', 'type': 'archaeological_site', 'country': 'Bahrain'},
    {'name': 'Dilmun Burial Mounds', 'type': 'archaeological_site', 'country': 'Bahrain'},
    {'name': 'Bahrain Pearling Trail', 'type': 'historical_site', 'country': 'Bahrain'},
    {'name': 'Arad Fort', 'type': 'fortress', 'country': 'Bahrain'},
    {'name': 'Riffa Fort', 'type': 'fortress', 'country': 'Bahrain'},
    {'name': 'Al Fateh Grand Mosque', 'type': 'religious_site', 'country': 'Bahrain'},
    {'name': 'Khamis Mosque', 'type': 'religious_site', 'country': 'Bahrain'},
    {'name': 'Bahrain National Museum', 'type': 'museum', 'country': 'Bahrain'},
    {'name': 'Tree of Life Bahrain', 'type': 'natural_site', 'country': 'Bahrain'},
    {'name': 'Bab Al Bahrain', 'type': 'historical_gate', 'country': 'Bahrain'},
    {'name': 'Manama', 'type': 'city', 'country': 'Bahrain'},
    {'name': 'Muharraq', 'type': 'city', 'country': 'Bahrain'},
    {'name': 'Riffa', 'type': 'city', 'country': 'Bahrain'},
    {'name': 'Barbar Temple', 'type': 'archaeological_site', 'country': 'Bahrain'},
    {'name': 'Saar', 'type': 'archaeological_site', 'country': 'Bahrain'},

    # 🇰🇼 KUWAIT (18 sites)
    {'name': 'Kuwait Towers', 'type': 'modern_landmark', 'country': 'Kuwait'},
    {'name': 'Grand Mosque Kuwait', 'type': 'religious_site', 'country': 'Kuwait'},
    {'name': 'Failaka Island', 'type': 'archaeological_site', 'country': 'Kuwait'},
    {'name': 'Kuwait National Museum', 'type': 'museum', 'country': 'Kuwait'},
    {'name': 'Red Fort Kuwait', 'type': 'fortress', 'country': 'Kuwait'},
    {'name': 'Seif Palace', 'type': 'historical_palace', 'country': 'Kuwait'},
    {'name': 'Souq Al-Mubarakiya', 'type': 'historical_market', 'country': 'Kuwait'},
    {'name': 'Tareq Rajab Museum', 'type': 'museum', 'country': 'Kuwait'},
    {'name': 'Kuwait City', 'type': 'city', 'country': 'Kuwait'},
    {'name': 'Hawalli', 'type': 'city', 'country': 'Kuwait'},
    {'name': 'Salmiya', 'type': 'city', 'country': 'Kuwait'},
    {'name': 'Jahra', 'type': 'city', 'country': 'Kuwait'},

    # 🇸🇩 SUDAN (25 sites)
    {'name': 'Meroë', 'type': 'ancient_city', 'country': 'Sudan'},
    {'name': 'Pyramids of Meroe', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'Gebel Barkal', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'Nuri', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'El-Kurru', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'Naqa', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'Musawwarat es-Sufra', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'Old Dongola', 'type': 'ancient_city', 'country': 'Sudan'},
    {'name': 'Kerma', 'type': 'ancient_city', 'country': 'Sudan'},
    {'name': 'Sai Island', 'type': 'archaeological_site', 'country': 'Sudan'},
    {'name': 'Suakin', 'type': 'historical_city', 'country': 'Sudan'},
    {'name': 'Omdurman', 'type': 'city', 'country': 'Sudan'},
    {'name': 'Tomb of the Mahdi', 'type': 'historical_site', 'country': 'Sudan'},
    {'name': 'Khalifa House Museum', 'type': 'museum', 'country': 'Sudan'},
    {'name': 'Sanganeb Marine National Park', 'type': 'natural_site', 'country': 'Sudan'},
    {'name': 'Khartoum', 'type': 'city', 'country': 'Sudan'},
    {'name': 'Kassala', 'type': 'city', 'country': 'Sudan'},
    {'name': 'Port Sudan', 'type': 'city', 'country': 'Sudan'},

    # 🇲🇷 MAURITANIA (19 sites)
    {'name': 'Chinguetti', 'type': 'ancient_city', 'country': 'Mauritania'},
    {'name': 'Ouadane', 'type': 'ancient_city', 'country': 'Mauritania'},
    {'name': 'Tichitt', 'type': 'ancient_city', 'country': 'Mauritania'},
    {'name': 'Oualata', 'type': 'ancient_city', 'country': 'Mauritania'},
    {'name': 'Banc d\'Arguin National Park', 'type': 'natural_site', 'country': 'Mauritania'},
    {'name': 'Terjit', 'type': 'oasis', 'country': 'Mauritania'},
    {'name': 'Nouakchott', 'type': 'city', 'country': 'Mauritania'},
    {'name': 'Port de Peche', 'type': 'cultural_site', 'country': 'Mauritania'},
    {'name': 'Richat Structure', 'type': 'natural_site', 'country': 'Mauritania'},
    {'name': 'Nouadhibou', 'type': 'city', 'country': 'Mauritania'},
    {'name': 'Zouérat', 'type': 'town', 'country': 'Mauritania'},
    {'name': 'Atar', 'type': 'town', 'country': 'Mauritania'},

    # 🇸🇴 SOMALIA (19 sites)
    {'name': 'Laas Geel', 'type': 'archaeological_site', 'country': 'Somalia'},
    {'name': 'Zeila', 'type': 'historical_city', 'country': 'Somalia'},
    {'name': 'Masjid al-Qiblatayn (Somalia)', 'type': 'religious_site', 'country': 'Somalia'},
    {'name': 'Mogadishu', 'type': 'city', 'country': 'Somalia'},
    {'name': 'Arba\'a Rukun Mosque', 'type': 'religious_site', 'country': 'Somalia'},
    {'name': 'Shanghai Old City', 'type': 'historical_district', 'country': 'Somalia'},
    {'name': 'Berbera', 'type': 'city', 'country': 'Somalia'},
    {'name': 'Iskushuban', 'type': 'historical_site', 'country': 'Somalia'},
    {'name': 'Fakr ad-Din Mosque', 'type': 'religious_site', 'country': 'Somalia'},
    {'name': 'Hargeisa', 'type': 'city', 'country': 'Somalia'},
    {'name': 'Bosaso', 'type': 'city', 'country': 'Somalia'},
    {'name': 'Kismayo', 'type': 'city', 'country': 'Somalia'},

    # 🇩🇯 DJIBOUTI (16 sites)
    {'name': 'Djibouti City', 'type': 'city', 'country': 'Djibouti'},
    {'name': 'Lake Assal', 'type': 'natural_site', 'country': 'Djibouti'},
    {'name': 'Lake Abbe', 'type': 'natural_site', 'country': 'Djibouti'},
    {'name': 'Day Forest', 'type': 'natural_site', 'country': 'Djibouti'},
    {'name': 'Tadjoura', 'type': 'city', 'country': 'Djibouti'},
    {'name': 'Moucha Island', 'type': 'natural_site', 'country': 'Djibouti'},
    {'name': 'Ali Sabieh', 'type': 'town', 'country': 'Djibouti'},
    {'name': 'Dikhil', 'type': 'town', 'country': 'Djibouti'},
    {'name': 'Obock', 'type': 'town', 'country': 'Djibouti'},
    {'name': 'Arta', 'type': 'town', 'country': 'Djibouti'},

    # 🇰🇲 COMOROS (16 sites)
    {'name': 'Moroni', 'type': 'city', 'country': 'Comoros'},
    {'name': 'Old Friday Mosque', 'type': 'religious_site', 'country': 'Comoros'},
    {'name': 'Mount Karthala', 'type': 'natural_site', 'country': 'Comoros'},
    {'name': 'Mutsamudu', 'type': 'city', 'country': 'Comoros'},
    {'name': 'Citadel of Mutsamudu', 'type': 'fortress', 'country': 'Comoros'},
    {'name': 'Domoni', 'type': 'historical_town', 'country': 'Comoros'},
    {'name': 'Moheli Marine Park', 'type': 'natural_site', 'country': 'Comoros'},
    {'name': 'Fomboni', 'type': 'town', 'country': 'Comoros'},
]


def auto_collect_all():
    """Automatically collect all sites and organize by country"""

    db = CountryDatabase()
    total = len(ALL_SITES)
    success = 0
    total_words = 0
    start_time = time.time()

    print("\n" + "=" * 100)
    print("🏛️  ARAB HERITAGE RAG COLLECTION - ORGANIZED BY COUNTRY")
    print("=" * 100)
    print(f"Total sites: {total}")
    print(f"Estimated time: ~{total * 40 // 60} minutes")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100 + "\n")
    print("☕ This will create ONE comprehensive file per country for your RAG system!\n")

    for i, site in enumerate(ALL_SITES, 1):
        print(f"[{i}/{total}] {site['name']} ({site['country']})")

        try:
            collector = HeritageCollector(
                site_name=site['name'],
                site_type=site['type'],
                country=site['country'],
                era=site.get('era')
            )

            data = collector.collect_all()

            if data['sources']:
                db.add_site(data)
                sources, words = collector.get_stats()
                print(f"    ✅ {sources} sources, {words:,} words → Added to {site['country']} database")
                success += 1
                total_words += words
            else:
                print(f"    ⚠️  No data found")

            # Progress updates
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / (elapsed / 60)
                remaining = (total - i) / rate
                print(f"\n📊 Progress: {i}/{total} ({(i / total) * 100:.1f}%)")
                print(f"⏱️  Elapsed: {elapsed / 60:.1f} min | Remaining: ~{remaining:.1f} min")
                print(f"💾 Total collected: {total_words:,} words\n")
                time.sleep(3)
            else:
                time.sleep(1.5)

        except Exception as e:
            print(f"    ❌ Error: {str(e)[:80]}")

    # Final summary
    elapsed = time.time() - start_time
    print(f"\n" + "=" * 100)
    print(f"✅ RAG COLLECTION COMPLETE!")
    print("=" * 100)
    print(f"Sites processed: {total}")
    print(f"Successfully collected: {success} ({(success / total) * 100:.1f}%)")
    print(f"Total words: {total_words:,}")
    print(f"Estimated tokens: ~{int(total_words * 1.3):,}")
    print(f"Total time: {elapsed / 60:.1f} minutes ({elapsed / 3600:.1f} hours)")
    print(f"\n📁 Output directory: arab_heritage_by_country/")
    print(f"   Each country has:")
    print(f"   - _COMPLETE_<country>.txt  ← Load this into your RAG! All sites in one file")
    print(f"   - _COMPLETE_<country>.json ← Structured metadata")
    print(f"   - individual .json files for each site")
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100 + "\n")

    return success, total_words


if __name__ == "__main__":
    print("\n🚀 Starting RAG-optimized collection in 5 seconds...")
    print("Press Ctrl+C to cancel\n")

    time.sleep(5)

    try:
        auto_collect_all()
        print("\n🎉 Done! Each country has ONE complete file - perfect for RAG!\n")
        print("Example: Search 'Jordan' → Get _COMPLETE_jordan.txt with ALL Jordan sites\n")
    except KeyboardInterrupt:
        print("\n\n❌ Collection cancelled by user\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}\n")