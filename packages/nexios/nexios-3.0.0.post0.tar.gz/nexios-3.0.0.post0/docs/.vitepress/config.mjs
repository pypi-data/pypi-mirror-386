import { defineConfig } from 'vitepress'

export default defineConfig({
 
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/./logo.png' }],
    ['meta', { name: 'theme-color', content: '#ff7e17' }],
    ['meta', { property: 'og:title', content: "Nexios - Python Web Framework" }],
    ['meta', { property: 'og:description', content: "Nexios is a modern, fast, and secure web framework for Python. It is designed to be easy to use and understand, while also being powerful and flexible." }],
    ['meta', { property: 'og:image', content: "/./logo.png" }],
    ['meta', { property: 'og:type', content: 'website' }],
  ],
  
  
  title: 'Nexios',
  base: "/nexios/",
  description: 'Nexios is a modern, fast, and secure web framework for Python. It is designed to be easy to use and understand, while also being powerful and flexible.',

  themeConfig: {
    siteTitle: 'Nexios',
    logo: '/logo.png',
    favicon: '/logo.png',
    themeSwitcher: true,

    socialLinks: [
      { icon: "github", link: "https://github.com/nexios-labs/nexios" },
      { icon: "twitter", link: "https://twitter.com/nexioslabs" },
    ],

    search: {
      provider: 'local'
    },

    nav: [
      { text: 'Intro', link: '/intro' },
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'Examples', link: '/api-examples' },
      { text : "Community", link:"/community"},
      { text: "Discussions", link:"https://github.com/orgs/nexios-labs/discussions"},
      { text: 'Team', link: 'team' },
      {
        text: 'v3.0.0-alpha.1  (Latest)',
        items: [
          { text: 'v3.0.0-alpha.1', link: '/guide/getting-started' },
          { text: 'v2.11.1', link: '/v2/guide/getting-started' },
          { text: 'Changelog', link: 'https://github.com/nexios-labs/nexios/blob/CHANGELOG.md' },
          { text: 'Contributing', link: '/community/contribution-guide' },
        ]
      }
    ],

    sidebar: {
      '/intro/': [
        { text: 'What is Nexios?', link: '/intro' },
        { text: "What is Asgi?", link: '/intro/asgi' },
        { text: 'Nexios And FastAPI', link: '/intro/nexios-and-fastapi' },
        { text: "Quick Start", link: '/intro/quick-start' },
        { text : "Core Concepts", link: '/intro/concepts' },
        { text : "Async Python", link: '/intro/async-python' },
        {text: 'Migrating To Nexios',link: '/intro/migrating-to-nexios'},
      ],
      '/community/': [
        { text: 'Welcome', link: '/community' },
        { text: 'FAQ', link: '/community/faq' },
        { text : "Contribution Guide", link:"/community/contribution-guide"},
        { text: 'Discussions', link: 'https://github.com/orgs/nexios-labs/discussions' },
        { text: 'Team', link: '/team' },
      ],
      '/v2/guide/': [
        
        { text: 'Getting Started', link: '/guide/getting-started' },
        { text: 'CLI', link: '/guide/cli' },
        { text : "Why Nexios?", link: '/guide/why-nexios' },
        {
          text: 'Core Concepts',
          collapsed: false,
          items: [
            { text: 'Routing', link: '/v2/guide/routing' },
            { text: 'Handlers', link: '/v2/guide/handlers' },
            { text: 'Startups and Shutdowns', link: '/v2/guide/startups-and-shutdowns' },
            { text: 'Request Inputs', link: '/v2/guide/request-inputs' },
            { text: 'Configuration', link: '/v2/guide/configuration' },
            { text: 'Sending Responses', link: '/v2/guide/sending-responses' },
            { text: 'Routers and Subapps', link: '/v2/guide/routers-and-subapps' },
            { text: 'Middleware', link: '/v2/guide/middleware' },
          ] 
        },
        {
          text: 'Request Lifecycle',
          collapsed: false,
          items: [
            { text: 'Cookies', link: '/v2/guide/cookies' },
            { text: 'Headers', link: '/v2/guide/headers' },
            { text: 'Sessions', link: '/v2/guide/sessions' },
            { text: 'Request Info', link: '/v2/guide/request-info' },
          ]
        },
        {
          text: 'Advanced Topics',
          collapsed: false,
          items: [
            { text: 'Error Handling', link: '/v2/guide/error-handling' },
            { text: 'Pagination', link: '/v2/guide/pagination' },
            { text: 'Authentication', link: '/v2/guide/authentication' },
            { text: "Handler Hooks", link: '/v2/guide/handler-hooks' },
            { text: 'Class Based Handlers', link: '/v2/guide/class-based-handlers' },
            { text: 'Events', link: '/v2/guide/events' },
            { text: 'Streaming Response',  link: '/v2/guide/streaming-response' },
            { text: 'Dependency Injection', link: '/v2/guide/dependency-injection' },
            { text : "Templating", link:"/v2/guide/templating/index"},
            { text: 'Static Files', link: '/v2/guide/static-files' },
            { text: 'File Upload', link: '/v2/guide/file-upload' },
            { text: 'Cors', link: '/v2/guide/cors' },
            { text: 'CSRF', link: '/v2/guide/csrf' },  
            { text: 'File Router', link: '/v2/guide/file-router' },
            { text: 'Concurrency Utilities', link: '/v2/guide/concurrency' },
            { text: 'Security', link: '/v2/guide/security' },
            { text: 'Pydantic Integration', link: '/v2/guide/pydantic-integration' },
          ]
        },
        {
          text: 'Websockets',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/v2/guide/websockets/index' },
            { text: 'Channels', link: '/v2/guide/websockets/channels' },
            { text: 'Groups', link: '/v2/guide/websockets/groups' },
            { text: 'Events', link: '/v2/guide/websockets/events' },
            { text: 'Consumer', link: '/v2/guide/websockets/consumer' },
          ]
        },
        {
          text: 'OpenAPI',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/v2/guide/openapi/index' },
            { text: 'Response Models with Pydantic', link: '/v2/guide/openapi/response-models' },
            { text: 'Request Schemas', link: '/v2/guide/openapi/request-schemas' },
            { text: 'Request Parameters', link: '/v2/guide/openapi/request-parameters' },
            { text: 'Customizing OpenAPI Config', link: '/v2/guide/openapi/customizing-openapi-configuration' },
            { text: 'Authentication Docs', link: '/v2/guide/openapi/authentication-documentation' },
          ]
        }
      ],
      '/guide/': [
        
        { text: 'Getting Started', link: '/guide/getting-started' },
        { text: 'CLI', link: '/guide/cli' },
        { text : "Why Nexios?", link: '/guide/why-nexios' },
        {
          text: 'Core Concepts',
          collapsed: false,
          items: [
            { text: 'Routing', link: '/guide/routing' },
            { text: 'Handlers', link: '/guide/handlers' },
            { text: 'Startups and Shutdowns', link: '/guide/startups-and-shutdowns' },
            { text: 'Request Inputs', link: '/guide/request-inputs' },
            { text: 'Configuration', link: '/guide/configuration' },
            { text: 'Sending Responses', link: '/guide/sending-responses' },
            { text: 'Routers and Subapps', link: '/guide/routers-and-subapps' },
            { text: 'Middleware', link: '/guide/middleware' },
          ] 
        },
        {
          text: 'Request Lifecycle',
          collapsed: false,
          items: [
            { text: 'Cookies', link: '/guide/cookies' },
            { text: 'Headers', link: '/guide/headers' },
            { text: 'Sessions', link: '/guide/sessions' },
            { text: 'Request Info', link: '/guide/request-info' },
          ]
        },
        {
          text: 'Advanced Topics',
          collapsed: false,
          items: [
            { text: 'Error Handling', link: '/guide/error-handling' },
            { text: 'Pagination', link: '/guide/pagination' },
            { text: 'Authentication', link: '/guide/authentication' },
            { text: "Handler Hooks", link: '/guide/handler-hooks' },
            { text: 'Class Based Handlers', link: '/guide/class-based-handlers' },
            { text: 'Events', link: '/guide/events' },
            { text: 'Streaming Response',  link: '/guide/streaming-response' },
            { text: 'Dependency Injection', link: '/guide/dependency-injection' },
            { text : "Templating", link:"/guide/templating/index"},
            { text: 'Static Files', link: '/guide/static-files' },
            { text: 'File Upload', link: '/guide/file-upload' },
            { text: 'Cors', link: '/guide/cors' },
            { text: 'CSRF', link: '/guide/csrf' },
            { text: 'Concurrency Utilities', link: '/guide/concurrency' },
            { text: 'Security', link: '/guide/security' },
            { text: 'Pydantic Integration', link: '/guide/pydantic-integration' },
          ]
        },
        {
          text: 'Websockets',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/guide/websockets/index' },
            { text: 'Channels', link: '/guide/websockets/channels' },
            { text: 'Groups', link: '/guide/websockets/groups' },
            { text: 'Events', link: '/guide/websockets/events' },
            { text: 'Consumer', link: '/guide/websockets/consumer' },
          ]
        },
        {
          text: 'OpenAPI',
          collapsed: false,
          items: [
            { text: 'Overview', link: '/guide/openapi/index' },
            { text: 'Response Models with Pydantic', link: '/guide/openapi/response-models' },
            { text: 'Request Schemas', link: '/guide/openapi/request-schemas' },
            { text: 'Request Parameters', link: '/guide/openapi/request-parameters' },
            { text: 'Customizing OpenAPI Config', link: '/guide/openapi/customizing-openapi-configuration' },
            { text: 'Authentication Docs', link: '/guide/openapi/authentication-documentation' },
          ]
        }
      ]
     
    }
  },

  markdown: {
    // lineNumbers: true
  },

  ignoreDeadLinks: true,
})