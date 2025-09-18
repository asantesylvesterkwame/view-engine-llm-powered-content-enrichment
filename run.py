def main():
    import argparse
    import logging
    import sys

    parser = argparse.ArgumentParser(description="LLM-powered content enrichment for Markdown articles.")
    parser.add_argument('--article_path', required=True, help='Path to the input Markdown article')
    parser.add_argument('--keywords_path', required=True, help='Path to the keywords .txt file')
    parser.add_argument('--output_path', default='enriched_article.md', help='Path to save the enriched Markdown')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    try:
        article = load_article(args.article_path)
        keywords = load_keywords(args.keywords_path)
        brand_rules = load_brand_rules()
        media_candidates = query_media_db()
        link_candidates = query_links_db()
        llm_response = call_llm(article, keywords, media_candidates, link_candidates, brand_rules)
        logging.info(f"LLM raw response: {llm_response}")
        enrichments = parse_llm_response(llm_response)
        logging.info(f"Parsed enrichments: {enrichments}")
        enriched_article = assemble_article(article, enrichments)
        save_article(enriched_article, args.output_path)
        logging.info(f"Enriched article saved to {args.output_path}")
    except Exception as e:
        logging.exception(f"Error during enrichment: {e}")


def load_article(article_path):
    with open(article_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_keywords(keywords_path):
    with open(keywords_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_brand_rules(path='resources/brand_rules.txt'):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def query_media_db(db_path='resources/media.db'):
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''SELECT id, url, title, description, tags FROM images''')
    images = [dict(zip(['id', 'url', 'title', 'description', 'tags'], row)) for row in cur.fetchall()]
    cur.execute('''SELECT id, url, title, description, tags FROM videos''')
    videos = [dict(zip(['id', 'url', 'title', 'description', 'tags'], row)) for row in cur.fetchall()]
    conn.close()
    return images + videos

def query_links_db(db_path='resources/links.db'):
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''SELECT id, url, title, description, topic_tags, type FROM resources''')
    links = [dict(zip(['id', 'url', 'title', 'description', 'topic_tags', 'type'], row)) for row in cur.fetchall()]
    conn.close()
    return links

def call_llm(article, keywords, media_candidates, link_candidates, brand_rules):
    import requests
    import json
    api_key = "-API-KEY-"
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = f"""
You are an expert content editor. Given the following article, media candidates, link candidates, keywords, and brand rules, select:
- 1 hero image (from media),
- 1 in-context image or video (from media),
- 2 links (from links), each with LLM-generated anchor text around a provided keyword.
Return a JSON object with keys: hero_image, in_context_media, links (list of 2 with anchor_text, keyword, url, insertion_point).
Follow all brand rules for alt text and voice.

ARTICLE: {article}
KEYWORDS: {keywords}
MEDIA_CANDIDATES: {json.dumps(media_candidates)[:3000]}
LINK_CANDIDATES: {json.dumps(link_candidates)[:3000]}
BRAND_RULES: {brand_rules}
Respond ONLY with the JSON object.
"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800
    }
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    return content

def parse_llm_response(llm_response):
    import json
    try:
        start = llm_response.find('{')
        end = llm_response.rfind('}') + 1
        json_str = llm_response[start:end]
        data = json.loads(json_str)
        assert 'hero_image' in data and 'in_context_media' in data and 'links' in data
        assert isinstance(data['links'], list) and len(data['links']) == 2
        return data
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {e}\nRaw: {llm_response}")

def assemble_article(article, enrichments):
    hero = enrichments['hero_image']
    hero_md = f"![{hero.get('alt', hero.get('title',''))}]({hero['url']})\n\n"
    content = hero_md + article
    in_media = enrichments['in_context_media']
    in_media_md = f"![{in_media.get('alt', in_media.get('title',''))}]({in_media['url']})\n\n"
    paras = content.split('\n\n', 1)
    if len(paras) > 1:
        content = paras[0] + '\n\n' + in_media_md + paras[1]
    else:
        content += '\n\n' + in_media_md
    import re
    for link in enrichments['links']:
        anchor = f"[{link['anchor_text']}]({link['url']})"
        keyword = link['keyword']
        insertion_point = link.get('insertion_point')
        inserted = False
        if insertion_point:
            lines = content.splitlines(keepends=True)
            for idx, line in enumerate(lines):
                if insertion_point.lower() in line.lower():
                    lines.insert(idx + 1, f"{anchor}\n")
                    content = ''.join(lines)
                    inserted = True
                    break
        if not inserted:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            if pattern.search(content):
                content = pattern.sub(anchor, content, count=1)
                inserted = True
        if not inserted:
            content += f"\n\n{anchor}"
    return content

def save_article(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    main()
