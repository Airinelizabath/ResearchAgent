import Parser from 'rss-parser';

// Initialize parser
const parser = new Parser();

// Standard topics supported by Google News
export const TOPICS = {
  WORLD: 'WORLD',
  NATION: 'NATION',
  BUSINESS: 'BUSINESS',
  TECHNOLOGY: 'TECHNOLOGY',
  ENTERTAINMENT: 'ENTERTAINMENT',
  SPORTS: 'SPORTS',
  SCIENCE: 'SCIENCE',
  HEALTH: 'HEALTH'
};

// Aliases for user-friendly matching
export const TOPIC_ALIASES = {
  world: 'WORLD',
  nation: 'NATION',
  national: 'NATION',
  business: 'BUSINESS',
  biz: 'BUSINESS',
  technology: 'TECHNOLOGY',
  tech: 'TECHNOLOGY',
  entertainment: 'ENTERTAINMENT',
  sports: 'SPORTS',
  sport: 'SPORTS',
  science: 'SCIENCE',
  sci: 'SCIENCE',
  health: 'HEALTH'
};

/**
 * Normalizes user input into a valid topic code.
 * @param {string} topic 
 * @returns {string|null}
 */
export function normalizeTopic(topic) {
  if (!topic) return null;
  const lower = topic.toLowerCase().trim();
  return TOPIC_ALIASES[lower] || null;
}

/**
 * Helper to split Google News title into clean title and source
 * Example: "NASA Mars Rover - Space.com" -> { title: "NASA Mars Rover", source: "Space.com" }
 * @param {string} rawTitle 
 * @returns {{title: string, source: string}}
 */
export function parseTitle(rawTitle) {
  if (!rawTitle) {
    return { title: '', source: 'Unknown' };
  }
  
  const index = rawTitle.lastIndexOf(' - ');
  if (index !== -1) {
    const title = rawTitle.substring(0, index).trim();
    const source = rawTitle.substring(index + 3).trim();
    return { title: title, source: source };
  }
  
  return { title: rawTitle, source: 'Google News' };
}

/**
 * Builds the Google News RSS URL based on given options.
 * @param {object} options 
 * @returns {string}
 */
export function getFeedUrl(options) {
  const opts = options || {};
  const topic = opts.topic;
  const search = opts.search;
  const lang = opts.lang || 'en';
  const country = opts.country || 'US';
  
  const hl = lang.toLowerCase() + '-' + country.toUpperCase();
  const gl = country.toUpperCase();
  const ceid = country.toUpperCase() + ':' + lang.toLowerCase();
  
  const queryParams = 'hl=' + hl + '&gl=' + gl + '&ceid=' + ceid;
  
  if (search) {
    return 'https://news.google.com/rss/search?q=' + encodeURIComponent(search) + '&' + queryParams;
  }
  
  if (topic) {
    const matchedTopic = normalizeTopic(topic) || topic.toUpperCase();
    return 'https://news.google.com/rss/headlines/section/topic/' + matchedTopic + '?' + queryParams;
  }
  
  // Default to top headlines
  return 'https://news.google.com/rss?' + queryParams;
}

/**
 * Fetches and parses the Google News RSS feed.
 * @param {object} options 
 * @returns {Promise<object[]>}
 */
export async function fetchNews(options) {
  const url = getFeedUrl(options);
  const limit = (options && options.limit) || 10;
  
  try {
    const feed = await parser.parseURL(url);
    const items = feed.items || [];
    
    // Map items to a clean format
    const results = [];
    const count = Math.min(items.length, limit);
    for (let i = 0; i < count; i++) {
      const item = items[i];
      const parsed = parseTitle(item.title);
      results.push({
        title: parsed.title,
        source: parsed.source,
        link: item.link,
        pubDate: item.pubDate || item.isoDate || 'Unknown Date',
        snippet: item.contentSnippet || item.content || ''
      });
    }
    return results;
  } catch (error) {
    throw new Error('Failed to fetch news from Google RSS feed: ' + error.message);
  }
}
