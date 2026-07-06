import prompts from 'prompts';
import pc from 'picocolors';
import open from 'open';
import { fetchNews, TOPICS, normalizeTopic } from './api.js';

/**
 * Text wrapping utility.
 * @param {string} text 
 * @param {number} maxLength 
 * @returns {string[]}
 */
export function wrapText(text, maxLength) {
  if (!text) return [];
  const words = text.split(' ');
  const lines = [];
  let currentLine = '';
  
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    if ((currentLine + word).length > maxLength) {
      if (currentLine) {
        lines.push(currentLine.trim());
      }
      currentLine = word + ' ';
    } else {
      currentLine += word + ' ';
    }
  }
  if (currentLine.trim()) {
    lines.push(currentLine.trim());
  }
  return lines;
}

/**
 * Renders a premium console banner.
 */
export function renderBanner() {
  console.log('\n' + pc.cyan('╔══════════════════════════════════════════════════════════╗'));
  console.log(pc.cyan('║') + pc.bold(pc.yellow('                  GOOGLE NEWS TERMINAL                    ')) + pc.cyan('║'));
  console.log(pc.cyan('║') + pc.gray('            Stay updated from your command line           ') + pc.cyan('║'));
  console.log(pc.cyan('╚══════════════════════════════════════════════════════════╝\n'));
}

/**
 * Renders a plain list of articles (used in non-interactive mode).
 * @param {object[]} articles 
 */
export function renderArticleList(articles) {
  if (!articles || articles.length === 0) {
    console.log(pc.red('No articles found.'));
    return;
  }
  
  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];
    const num = pc.green('[' + (i + 1) + ']');
    console.log(num + ' ' + pc.bold(article.title));
    console.log('    Source: ' + pc.yellow(article.source) + ' | Date: ' + pc.gray(article.pubDate));
    console.log('    Link:   ' + pc.blue(pc.underline(article.link)));
    console.log('');
  }
}

/**
 * Displays details of a single article and provides actions.
 * @param {object} article 
 */
export async function viewArticleDetails(article) {
  while (true) {
    console.log('\n' + pc.cyan('──────────────────────────────────────────────────────────'));
    console.log(pc.bold(pc.yellow('ARTICLE DETAILS')));
    console.log(pc.cyan('──────────────────────────────────────────────────────────'));
    
    const wrappedTitle = wrapText(article.title, 65);
    for (let i = 0; i < wrappedTitle.length; i++) {
      console.log(pc.bold(wrappedTitle[i]));
    }
    
    console.log(pc.cyan('──────────────────────────────────────────────────────────'));
    console.log(pc.magenta('Publisher: ') + article.source);
    console.log(pc.magenta('Published: ') + article.pubDate);
    console.log(pc.magenta('Link:      ') + pc.blue(pc.underline(article.link)));
    console.log(pc.cyan('──────────────────────────────────────────────────────────\n'));
    
    const action = await prompts({
      type: 'select',
      name: 'choice',
      message: 'What would you like to do?',
      choices: [
        { title: '🌐 Open in browser', value: 'open' },
        { title: '↩️ Back to article list', value: 'back' }
      ],
      initial: 0
    });
    
    if (action.choice === undefined || action.choice === 'back') {
      break;
    }
    
    if (action.choice === 'open') {
      console.log(pc.cyan('\nOpening in default browser... '));
      try {
        await open(article.link);
      } catch (e) {
        console.log(pc.red('Failed to open browser. Please copy the link above.'));
      }
    }
  }
}

/**
 * Handles fetching news and managing the browse/selection process.
 * @param {object} fetchOptions 
 */
export async function handleFetchAndBrowse(fetchOptions) {
  console.log(pc.cyan('\nFetching the latest news...'));
  
  let articles;
  try {
    articles = await fetchNews(fetchOptions);
  } catch (error) {
    console.log(pc.red('\nError fetching news: ' + error.message + '\n'));
    return;
  }
  
  console.log(pc.green('Fetched ' + articles.length + ' articles.\n'));
  
  if (articles.length === 0) {
    console.log(pc.yellow('No articles found matching the criteria.\n'));
    return;
  }
  
  while (true) {
    const choices = [];
    for (let i = 0; i < articles.length; i++) {
      const article = articles[i];
      const limitTitle = article.title.length > 60 
        ? article.title.substring(0, 57) + '...' 
        : article.title;
      choices.push({
        title: (i + 1) + '. ' + limitTitle + ' [' + pc.yellow(article.source) + ']',
        value: i
      });
    }
    
    choices.push({ title: pc.gray('↩️ Back to main menu'), value: 'back' });
    
    const selection = await prompts({
      type: 'select',
      name: 'index',
      message: 'Select an article to view details:',
      choices: choices,
      initial: 0
    });
    
    if (selection.index === undefined || selection.index === 'back') {
      break;
    }
    
    const article = articles[selection.index];
    await viewArticleDetails(article);
  }
}

/**
 * Starts the main interactive loop.
 * @param {object} defaultOptions 
 */
export async function startInteractive(defaultOptions) {
  const opts = defaultOptions || {};
  renderBanner();
  
  const state = {
    lang: opts.lang || 'en',
    country: opts.country || 'US',
    limit: opts.limit || 10
  };
  
  while (true) {
    const response = await prompts({
      type: 'select',
      name: 'action',
      message: 'What would you like to read today?',
      choices: [
        { title: '📰 Top Headlines', value: 'top' },
        { title: '🔍 Search News', value: 'search' },
        { title: '🏷️ Browse by Topic', value: 'topic' },
        { title: '❌ Exit', value: 'exit' }
      ],
      initial: 0
    });
    
    if (response.action === undefined || response.action === 'exit') {
      console.log(pc.cyan('\nThank you for using Google News Terminal. Goodbye!\n'));
      break;
    }
    
    if (response.action === 'top') {
      await handleFetchAndBrowse({ 
        lang: state.lang, 
        country: state.country, 
        limit: state.limit 
      });
    } else if (response.action === 'search') {
      const searchPrompt = await prompts({
        type: 'text',
        name: 'query',
        message: 'Enter search term:',
        validate: function(value) {
          return value.trim().length > 0 ? true : 'Please enter a search query.';
        }
      });
      
      if (searchPrompt.query !== undefined) {
        await handleFetchAndBrowse({
          search: searchPrompt.query,
          lang: state.lang,
          country: state.country,
          limit: state.limit
        });
      }
    } else if (response.action === 'topic') {
      const topicChoices = Object.keys(TOPICS).map(function(key) {
        return {
          title: key.charAt(0) + key.slice(1).toLowerCase(),
          value: key
        };
      });
      
      const topicPrompt = await prompts({
        type: 'select',
        name: 'topic',
        message: 'Select a topic:',
        choices: topicChoices
      });
      
      if (topicPrompt.topic !== undefined) {
        await handleFetchAndBrowse({
          topic: topicPrompt.topic,
          lang: state.lang,
          country: state.country,
          limit: state.limit
        });
      }
    }
  }
}
