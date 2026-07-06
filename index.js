#!/usr/bin/env node

import { program } from 'commander';
import pc from 'picocolors';
import { fetchNews } from './lib/api.js';
import { renderArticleList, startInteractive } from './lib/ui.js';

program
  .name('google-news')
  .description('A command line interface for Google News RSS feeds')
  .version('1.0.0')
  .option('-t, --top', 'fetch top headlines')
  .option('-s, --search <query>', 'search news stories')
  .option('-o, --topic <name>', 'fetch news for a specific topic (world, tech, business, sports, science, health, entertainment, nation)')
  .option('-l, --limit <number>', 'limit the number of articles shown', (val) => parseInt(val, 10), 10)
  .option('-c, --country <code>', 'two-letter country code (e.g., US, GB, IN)', 'US')
  .option('-g, --lang <code>', 'two-letter language code (e.g., en, es, fr)', 'en')
  .option('-i, --interactive', 'run in interactive mode (default if no fetching options provided)');

program.parse(process.argv);

const options = program.opts();

async function main() {
  // If interactive is explicitly set, or no actions (top, search, topic) are provided, go interactive
  const isInteractive = options.interactive || (!options.top && !options.search && !options.topic);

  if (isInteractive) {
    await startInteractive({
      lang: options.lang,
      country: options.country,
      limit: options.limit
    });
  } else {
    // Non-interactive CLI output
    try {
      console.log(pc.cyan('\nFetching stories from Google News [Country: ' + options.country.toUpperCase() + ', Lang: ' + options.lang.toLowerCase() + ']...'));
      
      const articles = await fetchNews({
        topic: options.topic,
        search: options.search,
        lang: options.lang,
        country: options.country,
        limit: options.limit
      });
      
      console.log(pc.green('Fetched ' + articles.length + ' articles:\n'));
      renderArticleList(articles);
    } catch (error) {
      console.error(pc.red('\nError: ' + error.message + '\n'));
      process.exit(1);
    }
  }
}

main().catch(function(err) {
  console.error(pc.red('Fatal error: ' + err.stack));
  process.exit(1);
});
