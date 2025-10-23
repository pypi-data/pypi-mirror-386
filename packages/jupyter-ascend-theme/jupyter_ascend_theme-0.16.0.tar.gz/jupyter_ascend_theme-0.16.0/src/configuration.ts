export type Links = Array<{ label: string; href: string }>;

export type AppConfig = {
  appName: string;
  header: {
    isVisible: boolean;
    getInsulaAppsMenuLinks?: () => Promise<Links | undefined>;
    otherInfoMenuLinks?: Links;
    getExtraTopbarLinks?: () => Promise<Links | undefined>;
  };
};

export const appConfig: AppConfig = {
  appName: 'Insula Coding (Experiment)',
  header: {
    isVisible: true,
    getInsulaAppsMenuLinks: async () => {
      let linksFromJupyterHubEnvVariables: Links | undefined;

      try {
        const response = await fetch('/hub/home');
        const textResponse = await response.text();

        /**
         * Regex to extract the window.__APP_MENU_LINKS__ JSON string from passed to the JupyterHub page
         *
         * window\.__APP_MENU_LINKS__ -> Matches the literal string window.__APP_MENU_LINKS__
         * \s*=\s*                -> Matches the "=" with any space around it
         * (...);                 -> Capturing group:
         * \[                     -> The intial square bracket
         * [\s\S]*?               -> [\s\S] matches any whitespace or non-whitespace character, *? matches the previous token unlimited times
         * \]                     -> The final square bracket
         * ;                      -> The semicolon
         * */
        const match = textResponse.match(
          /window\.__APP_MENU_LINKS__\s*=\s*(\[[\s\S]*?\]);/
        );

        if (match && match[1]) {
          /* match[1] is the first capture group */
          linksFromJupyterHubEnvVariables = JSON.parse(match[1]);
        }
      } catch (error) {
        console.warn('Failed to fetch menu links from /hub/home', error);
      }

      if (
        linksFromJupyterHubEnvVariables &&
        linksFromJupyterHubEnvVariables.length > 0
      ) {
        console.info('Using menu links from /hub/home');
        return linksFromJupyterHubEnvVariables;
      } else {
        return undefined;
      }
    },
    getExtraTopbarLinks: async () => {
      let linksFromJupyterHubEnvVariables: Links | undefined;

      try {
        const response = await fetch('/hub/home');
        const textResponse = await response.text();

        /**
         * Regex to extract the window.__HEADER_LINKS__ JSON string from passed to the JupyterHub page
         *
         * window\.__HEADER_LINKS__ -> Matches the literal string window.__HEADER_LINKS__
         * \s*=\s*                -> Matches the "=" with any space around it
         * (...);                 -> Capturing group:
         * \[                     -> The intial square bracket
         * [\s\S]*?               -> [\s\S] matches any whitespace or non-whitespace character, *? matches the previous token unlimited times
         * \]                     -> The final square bracket
         * ;                      -> The semicolon
         * */
        const match = textResponse.match(
          /window\.__HEADER_LINKS__\s*=\s*(\[[\s\S]*?\]);/
        );

        if (match && match[1]) {
          /* match[1] is the first capture group */
          linksFromJupyterHubEnvVariables = JSON.parse(match[1]);
        }
      } catch (error) {
        console.warn('Failed to fetch header links from /hub/home', error);
      }

      if (
        linksFromJupyterHubEnvVariables &&
        linksFromJupyterHubEnvVariables.length > 0
      ) {
        console.info('Using header links from /hub/home');
        return linksFromJupyterHubEnvVariables;
      } else {
        return undefined;
      }
    }
    // otherInfoMenuLinks: [
    //   {
    //     label: 'Vision',
    //     href: 'https://earthcare.pal.preop.esa-maap.org/vision'
    //   },
    //   {
    //     label: 'Documenation',
    //     href: 'https://earthcare.pal.preop.esa-maap.org/doc'
    //   },
    //   {
    //     label: 'ESA TellUS',
    //     href: 'https://earthcare.pal.preop.esa-maap.org/ESA TellUS'
    //   }
    // ]
  }
};
