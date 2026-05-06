from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Product, Category, ProductImage
from decimal import Decimal
import os
import json
import logging

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "Stroom Besparen": {
        "slug": "stroom-besparen",
        "icon": "⚡",
        "subcategories": [
            {"name": "Stand-by Verbruik", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/standby-verbruik/"},
            {"name": "Tijdschakelklokken", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/tijdschakelklokken/"},
            {"name": "Energiemeters", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/energiemeters/"},
            {"name": "Stekkerdozen", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/stekkerdozen/"},
            {"name": "Sensoren", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/sensoren/"},
            {"name": "Pompschakelaars", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/pompschakelaar/"},
            {"name": "Smarthome Producten", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/smarthome/"},
            {"name": "Wassen & Drogen", "url": "https://www.eco-groothandel.nl/energie-en-water/stroombesparing/wassen-en-drogen/"},
        ],
    },
    "Gas Besparen": {
        "slug": "gas-besparen",
        "icon": "🔥",
        "subcategories": [
            {"name": "Deurdrangers", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/deurdrangers/"},
            {"name": "Radiatorfolie", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/radiatorfolie/"},
            {"name": "Tochtband", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/tochtwering/"},
            {"name": "Brievenbusborstels", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/brievenbusborstel/"},
            {"name": "Deurborstels", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/deurborstels/"},
            {"name": "Slimme Thermostaten", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/slimme-thermostaten/"},
            {"name": "Radiatorventilator", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/radiator-ventilator/"},
            {"name": "Reflectiefolie", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/reflectiefolie/"},
            {"name": "Isolatiefolie", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/isolatiefolie/"},
            {"name": "Kit & Purschuim", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/kit-en-purschuim/"},
            {"name": "Elektrisch Verwarmen", "url": "https://www.eco-groothandel.nl/energie-en-water/gasbesparing/elektrisch-verwarmen/"},
        ],
    },
    "Water Besparen": {
        "slug": "water-besparen",
        "icon": "💧",
        "subcategories": [
            {"name": "Douche", "url": "https://www.eco-groothandel.nl/energie-en-water/waterbesparing/douche/"},
            {"name": "Kraan", "url": "https://www.eco-groothandel.nl/energie-en-water/waterbesparing/kraan/"},
            {"name": "Toilet", "url": "https://www.eco-groothandel.nl/energie-en-water/waterbesparing/toilet/"},
            {"name": "Douchecoach", "url": "https://www.eco-groothandel.nl/energie-en-water/waterbesparing/douchecoach/"},
        ],
    },
    "Verlichting": {
        "slug": "verlichting",
        "icon": "💡",
        "subcategories": [
            {"name": "Ledlampen E27", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/led/e27/"},
            {"name": "Ledlampen E14", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/led/e14/"},
            {"name": "Ledlampen GU10", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/led/gu10/"},
            {"name": "Ledlampen G4", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/led/g4led/"},
            {"name": "Ledlampen G9", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/led/g9led/"},
            {"name": "Ledlampen GU 5.3", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/led/g5-3led/"},
            {"name": "Ledbuizen", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/ledbuizen/"},
            {"name": "Leddimmers", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/leddimmers/"},
            {"name": "Slimme Verlichting", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/smart-lighting/"},
            {"name": "Armaturen", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/armatuur/"},
            {"name": "Nachtlampjes", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/nachtlampjes/"},
            {"name": "Tuinverlichting", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/tuinverlichting/"},
            {"name": "Buitenverlichting", "url": "https://www.eco-groothandel.nl/energie-en-water/verlichting/buitenverlichting/"},
        ],
    },
    "Klimaat": {
        "slug": "klimaat",
        "icon": "🌡️",
        "subcategories": [
            {"name": "Ventilatoren", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/ventilatoren/"},
            {"name": "Folies", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/folies/"},
            {"name": "Tochtwering", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/tochtwering/"},
            {"name": "Meten & Monitoren", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/meten-en-monitoren/"},
            {"name": "Horren & Klamboes", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/horren-en-klamboes/"},
            {"name": "Waterbesparing", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/waterbesparing/"},
            {"name": "Zonwering", "url": "https://www.eco-groothandel.nl/energie-en-water/klimaat/zonwering/"},
            {"name": "Zonnepanelen & Accu's", "url": "https://www.eco-groothandel.nl/energie-en-water/verwarming-en-koeling/zonnepanelen-en-accu/"},
        ],
    },
    "Meten": {
        "slug": "meten",
        "icon": "📏",
        "subcategories": [
            {"name": "Thermostaten", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/thermostaten/"},
            {"name": "CO2 Meters", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/co2-meters/"},
            {"name": "CO Meters", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/co-meters/"},
            {"name": "Hygrometers", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/hygrometers/"},
            {"name": "Thermometers", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/thermometers/"},
            {"name": "Slimme Meter Uitlezen", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/slimme-meter-uitlezen/"},
            {"name": "Energiemeters", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/energiemeters/"},
            {"name": "Rookmelders", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/rookmelders/"},
            {"name": "Waterverbruik", "url": "https://www.eco-groothandel.nl/energie-en-water/meten/waterverbruik/"},
        ],
    },
    "Energiebespaarbox": {
        "slug": "energiebespaarbox",
        "icon": "📦",
        "subcategories": [
            {"name": "Energiebespaarboxen", "url": "https://www.eco-groothandel.nl/energie-en-water/energiebesparing/energiebespaarbox/"},
            {"name": "Bulk producten", "url": "https://www.eco-groothandel.nl/energie-en-water/bulk-producten-energiecoach/"},
        ],
    },
    "Installatie": {
        "slug": "installatie",
        "icon": "🔧",
        "subcategories": [
            {"name": "Vloerverwarming", "url": "https://www.eco-groothandel.nl/bouwen-klussen/installatie/vloerverwarming/"},
            {"name": "Wandverwarming", "url": "https://www.eco-groothandel.nl/bouwen-klussen/installatie/wandverwarming/"},
            {"name": "CV-ketels", "url": "https://www.eco-groothandel.nl/bouwen-klussen/installatie/cv-ketels/"},
            {"name": "Projecten", "url": "https://www.eco-groothandel.nl/bouwen-klussen/installatie/projecten/"},
            {"name": "Energiebesparing", "url": "https://www.eco-groothandel.nl/bouwen-klussen/installatie/energiebesparing/"},
        ],
    },
}

class Command(BaseCommand):
    help = "Scrape ALL products and deep details from eco-groothandel.nl"

    def add_arguments(self, parser):
        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="Alleen een specifieke hoofdcategorie scrapen",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Alleen tellen, niet opslaan in de database",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max aantal producten om te scrapen (voor testen)",
        )
        parser.add_argument(
            "--url",
            type=str,
            default=None,
            help="Scrape één specifieke product-URL",
        )

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        from playwright.sync_api import sync_playwright

        target_category = options.get("category")
        dry_run = options.get("dry_run", False)
        limit = options.get("limit", 0)
        single_url = options.get("url")

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Actief"))

        self.stdout.write(self.style.HTTP_INFO(">> Start geavanceerde productsynchronisatie"))

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 800})
            page = context.new_page()

            # ── LOGIN ──────────────────────────────────────────────
            self.stdout.write("[LOGIN] Inloggen op eco-groothandel.nl ...")
            page.goto("https://www.eco-groothandel.nl/Inloggen.aspx")
            page.wait_for_timeout(2000)

            page.locator("#ContentPlaceHolderMain_Email").fill("info@ecozyhome.nl")
            page.locator("#ContentPlaceHolderMain_Wachtwoord").fill("ZX4nxT")
            page.locator("#ContentPlaceHolderMain_Wachtwoord").press("Enter")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            logged_in = page.evaluate("() => document.body.innerText.includes('Uitloggen')")
            if logged_in:
                self.stdout.write(self.style.SUCCESS("[OK] Succesvol ingelogd!"))
            else:
                self.stdout.write(self.style.ERROR("[FOUT] Login mislukt - mogelijk onjuiste prijzen"))

            # ── BEPAAL CATEGORIEËN ──────────────────────────────────
            categories_to_scrape = CATEGORY_MAP.items()
            if single_url:
                categories_to_scrape = [("Direct", {
                    "slug": "direct",
                    "icon": "🌿",
                    "subcategories": [{"name": "Direct", "url": single_url, "direct_product": True}],
                })]
            if target_category:
                categories_to_scrape = [(k, v) for k, v in CATEGORY_MAP.items() if target_category.lower() in k.lower()]

            total_new = 0
            total_updated = 0
            scraped_count = 0

            # ── HOOFD LOOP ──────────────────────────────────────────
            for main_name, main_data in categories_to_scrape:
                self.stdout.write(self.style.HTTP_INFO(f"\n[CAT] Hoofdcategorie: {main_name}"))

                for sub in main_data["subcategories"]:
                    if limit > 0 and scraped_count >= limit:
                        break

                    sub_name = sub["name"]
                    sub_url = sub["url"]
                    full_cat_name = f"{main_name} > {sub_name}"

                    self.stdout.write(f"  [SUB] {full_cat_name}")

                    if not dry_run and not sub.get("direct_product"):
                        # Create or get parent category
                        parent_cat, _ = Category.objects.get_or_create(
                            slug=main_data['slug'],
                            defaults={"name": main_name, "icon": main_data.get("icon", "🌿")}
                        )
                        # Create or get child category
                        child_slug = slugify(f"{main_data['slug']}-{sub_name}")[:50]
                        category_obj, _ = Category.objects.get_or_create(
                            slug=child_slug,
                            defaults={"name": sub_name, "parent": parent_cat}
                        )
                    else:
                        category_obj = None

                    # STAP 1: Verzamel alle URLs in deze subcategorie
                    product_urls = []
                    page_num = 1
                    if sub.get("direct_product"):
                        product_urls = [sub_url]
                        self.stdout.write("     Directe product-URL geselecteerd")
                    else:
                        while True:
                            url = sub_url if page_num == 1 else f"{sub_url}?p={page_num}"
                            self.stdout.write(f"     Verzamelen pagina {page_num}...")
                            try:
                                page.goto(url, timeout=15000)
                                page.wait_for_load_state("networkidle")
                            except Exception as e:
                                break

                            hrefs = page.evaluate("""() => {
                                let links = document.querySelectorAll('.productlistrow a.plink[id*="ProductName"]');
                                return Array.from(links).map(a => a.href);
                            }""")
                            
                            if not hrefs:
                                break
                            
                            for h in hrefs:
                                if h not in product_urls:
                                    product_urls.append(h)

                            has_next = page.evaluate(f"() => Array.from(document.querySelectorAll('a[href*=\"?p=\"]')).some(a => a.href.includes('?p={page_num + 1}'))")
                            if has_next:
                                page_num += 1
                            else:
                                break

                    self.stdout.write(f"     Gevonden URLs: {len(product_urls)}")

                    # STAP 2: Bezoek detailpagina's
                    for p_url in product_urls:
                        if limit > 0 and scraped_count >= limit:
                            break
                            
                        self.stdout.write(f"       Scraping: {p_url.split('/')[-1][:40]}...")
                        try:
                            page.goto(p_url, timeout=20000)
                            page.wait_for_timeout(1500)  # geef scripts even de tijd
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"       [WARN] Mislukt om te laden: {e}"))
                            continue

                        data = page.evaluate(r"""() => {
                            let title = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : '';
                            
                            let retail_price = null;
                            let adviesNodes = Array.from(document.querySelectorAll('*')).filter(el => el.innerText && el.innerText.includes('Adviesprijs incl.btw:'));
                            if(adviesNodes.length > 0) {
                                let text = adviesNodes[adviesNodes.length-1].parentElement.innerText;
                                let match = text.match(/(\d+)(?:[,.]\d{2}|,-)/);
                                if(match) retail_price = match[0].replace(',-', ',00');
                            }
                            
                            let purchase_price = null;
                            let mainPrice = document.querySelector('.price span') || document.querySelector('.product-price');
                            if(mainPrice) {
                                let match = mainPrice.innerText.match(/(\d+)(?:[,.]\d{2}|,-)/);
                                if(match) purchase_price = match[0].replace(',-', ',00');
                            }
                            
                            let descHtml = '';
                            let descEl = document.querySelector('#product-description') || document.querySelector('#details .product-description, #details');
                            let descNode = document.querySelector('#ContentPlaceHolderMain_Panel1');
                            if(descNode) {
                                // Clone it to not mess up the page
                                let clone = descNode.cloneNode(true);
                                
                                // Remove unwanted sections like "Andere uitvoeringen", "Gerelateerde producten"
                                let headers = clone.querySelectorAll('h2, h3, div');
                                headers.forEach(h => {
                                    let text = (h.innerText || '').toLowerCase();
                                    let id = (h.id || '').toLowerCase();
                                    let className = (h.className || '').toLowerCase();
                                    
                                    let shouldRemove = 
                                        text.includes('andere uitvoering') || 
                                        text.includes('misschien ook interessant') || 
                                        text.includes('bekijk ook') || 
                                        text.includes('gerelateerde') ||
                                        text.includes('productspecificaties') ||
                                        className.includes('header-product-details') ||
                                        id.includes('andereuitvoeringenpanel');
                                        
                                    if(shouldRemove && h.parentNode) {
                                        // Remove this header/div and all its siblings after it
                                        let sibling = h.nextSibling;
                                        while(sibling) {
                                            let next = sibling.nextSibling;
                                            sibling.remove();
                                            sibling = next;
                                        }
                                        // Also remove any preceding hr
                                        if(h.previousElementSibling && h.previousElementSibling.tagName.toLowerCase() === 'hr') {
                                            h.previousElementSibling.remove();
                                        }
                                        h.remove();
                                    }
                                });
                                
                                // Also remove any remaining tables (specs are usually in details-filter-table)
                                clone.querySelectorAll('table.details-filter-table').forEach(t => t.remove());
                                
                                descHtml = clone.innerHTML.trim();
                            } else if(descEl) {
                                // Clone to remove unwanted elements
                                let clone = descEl.cloneNode(true);
                                clone.querySelectorAll('select, form, input, button, script, style, .cart-actions, .omdooslist, [id*=Review], [id*=Offerte]').forEach(el => el.remove());
                                clone.querySelectorAll('.visible-xs, #ContentPlaceHolderMain_UpdatePanel4').forEach(el => el.remove());
                                clone.querySelectorAll('h2, h3, div').forEach(h => {
                                    let text = (h.innerText || '').toLowerCase();
                                    let className = (h.className || '').toLowerCase();
                                    if(text.includes('andere uitvoering') || text.includes('misschien ook interessant') || text.includes('bekijk ook') || text.includes('gerelateerde') || text.includes('productspecificaties') || className.includes('header-product-details')) {
                                        let sibling = h.nextSibling;
                                        while(sibling) {
                                            let next = sibling.nextSibling;
                                            sibling.remove();
                                            sibling = next;
                                        }
                                        h.remove();
                                    }
                                });
                                clone.querySelectorAll('table.details-filter-table').forEach(t => t.remove());
                                descHtml = clone.innerHTML.trim();
                            }
                            
                            let specs = {};
                            let tables = document.querySelectorAll('table');
                            tables.forEach(t => {
                                let rows = t.querySelectorAll('tr');
                                rows.forEach(r => {
                                    let cells = r.querySelectorAll('td, th');
                                    if(cells.length === 2) {
                                        specs[cells[0].innerText.trim()] = cells[1].innerText.trim();
                                    }
                                });
                            });

                            let documents = [];
                            document.querySelectorAll('#details a[href$=".pdf"], #product-description a[href$=".pdf"], a.pdf').forEach(a => {
                                let href = a.href;
                                if(href && !documents.some(doc => doc.url === href)) {
                                    documents.push({ title: (a.innerText || href.split('/').pop()).trim(), url: href });
                                }
                            });
                            if(documents.length) specs['_documents'] = documents;

                            let videos = [];
                            document.querySelectorAll('a[href*="youtube.com/embed"], a[href*="youtu.be"]').forEach(a => {
                                let href = a.href;
                                if(href && !videos.includes(href)) videos.push(href);
                            });
                            if(videos.length) specs['_videos'] = videos;

                            let detailText = document.querySelector('#product-description');
                            if(detailText) {
                                let text = detailText.innerText || '';
                                let sectionNames = ['Specificaties:', 'Inhoud set:', 'Richtlijn hoeveelheid:'];
                                let sections = [];
                                sectionNames.forEach((name, idx) => {
                                    let start = text.indexOf(name);
                                    if(start === -1) return;
                                    start += name.length;
                                    let end = text.length;
                                    sectionNames.forEach(other => {
                                        let otherIndex = text.indexOf(other, start);
                                        if(otherIndex !== -1 && otherIndex < end) end = otherIndex;
                                    });
                                    let body = text.slice(start, end).split('\n').map(line => line.trim()).filter(Boolean);
                                    if(body.length) sections.push({ title: name.replace(':', ''), lines: body });
                                });
                                if(sections.length) specs['_sections'] = sections;
                            }
                            
                            let brand = specs['Merk'] || specs['Merk:'] || '';
                            let ean = specs['EAN'] || specs['EAN code'] || specs['EAN:'] || '';
                            
                            let stock_status = '';
                            let stockNodes = Array.from(document.querySelectorAll('*')).filter(el => el.innerText && (el.innerText.toLowerCase().includes('levertijd:') || el.innerText.toLowerCase().includes('voorraad')));
                            if(stockNodes.length > 0) {
                                let validNodes = stockNodes.filter(n => n.innerText.length < 150);
                                if(validNodes.length > 0) {
                                    stock_status = validNodes[validNodes.length-1].innerText.trim();
                                }
                            }
                            
                            let images = [];
                            let imageKeys = [];
                            let addImage = (url) => {
                                if(!url) return;
                                let abs = new URL(url, window.location.href).href;
                                let lower = abs.toLowerCase();
                                let blocked = ['pixel', 'logo', 'shoppingcart', 'icon-vid', 'reviewster', 'cat-', 'radiatorfolie', '/nl.png'];
                                if(blocked.some(part => lower.includes(part))) return;
                                let key = decodeURIComponent(abs.split('/').pop() || abs).toLowerCase();
                                if(!imageKeys.includes(key)) {
                                    imageKeys.push(key);
                                    images.push(abs);
                                }
                            };
                            document.querySelectorAll('.main-image a[href], .main-image img, #ContentPlaceHolderMain_ProductImage').forEach(el => {
                                addImage(el.href || el.src || el.getAttribute('data-src'));
                            });
                            document.querySelectorAll('a[href*="images_content"], img[src*="images_content"]').forEach(el => {
                                addImage(el.href || el.src || el.getAttribute('data-src'));
                            });
                            document.querySelectorAll('.productimagediv img').forEach(img => addImage(img.src || img.getAttribute('data-src')));
                            let dropdownScript = Array.from(document.querySelectorAll('script')).map(s => s.innerText).find(text => text.includes('productdropdownimages'));
                            if(dropdownScript) {
                                Array.from(dropdownScript.matchAll(/\[(\d+),\s*"([^"]+)"\]/g)).forEach(match => addImage('https://www.eco-logisch.nl/images/' + match[2]));
                            }
                            
                            let options = {};
                            let selects = document.querySelectorAll('select');
                            let seenValues = [];
                            let optIdx = 1;
                            selects.forEach(s => {
                                let name = s.name || s.id || 'option';
                                if(name.includes('orderby') || name.includes('Beoordeling') || name.includes('review') || name.includes('aantal')) return;
                                let opts = Array.from(s.querySelectorAll('option')).map(o => o.innerText.trim()).filter(o => o && o !== 'Kies...');
                                if(opts.length > 0) {
                                    let valStr = JSON.stringify(opts);
                                    if(!seenValues.includes(valStr)) {
                                        seenValues.push(valStr);
                                        options[optIdx > 1 ? `Uitvoering ${optIdx}` : 'Uitvoering'] = opts;
                                        optIdx++;
                                    }
                                }
                            });
                            return { title, retail_price, purchase_price, descHtml, specs, brand, ean, stock_status, images, options };
                        }""")

                        if not data['title']:
                            continue

                        # Parse prijzen
                        r_price, p_price = None, None
                        if data['retail_price']:
                            try: r_price = Decimal(data['retail_price'].replace(',', '.'))
                            except: pass
                        if data['purchase_price']:
                            try: p_price = Decimal(data['purchase_price'].replace(',', '.'))
                            except: pass

                        if dry_run:
                            scraped_count += 1
                            continue

                        defaults = {
                            "title": data['title'],
                            "description": data['descHtml'],
                            "brand": data['brand'],
                            "ean": data['ean'][:50] if data['ean'] else '',
                            "purchase_price": p_price,
                            "retail_price": r_price,
                            "stock_status": data['stock_status'][:255] if data['stock_status'] else '',
                            "specifications": data['specs'],
                            "options": data['options'] if data['options'] else None,
                            "image_url": data['images'][0] if data['images'] else '',
                        }
                        if category_obj:
                            defaults["category"] = category_obj

                        product, created = Product.objects.update_or_create(
                            original_url=p_url,
                            defaults=defaults
                        )

                        if created:
                            total_new += 1
                        else:
                            total_updated += 1

                        # Save Images
                        if data['images']:
                            ProductImage.objects.filter(product=product).delete()
                            for img_url in data['images'][:12]:
                                ProductImage.objects.create(product=product, image_url=img_url)

                        scraped_count += 1

            browser.close()

        self.stdout.write(self.style.HTTP_INFO(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS("Synchronisatie voltooid!"))
        self.stdout.write(f"   Nieuw:      {total_new}")
        self.stdout.write(f"   Bijgewerkt: {total_updated}")

        if not dry_run:
            self.stdout.write(f"   Totaal in db: {Product.objects.count()}")
