/**
 * Jupyter notebook widgets for visualizing t-prompts structures.
 * Phase 0 & 1: Asset de-duplication and minimal static renderer
 */

import { initWidget } from './renderer';

declare const __TP_WIDGET_STYLES__: string;
declare const __TP_WIDGET_STYLES_HASH__: string;

const STYLES_HASH = typeof __TP_WIDGET_STYLES_HASH__ !== 'undefined' ? __TP_WIDGET_STYLES_HASH__ : 'dev';
const WIDGET_STYLES = typeof __TP_WIDGET_STYLES__ !== 'undefined' ? __TP_WIDGET_STYLES__ : '';

// Export version matching Python package
export const VERSION = '0.9.0-alpha';

// Store widget runtime on window for singleton pattern (Phase 0)
declare global {
  interface Window {
    __TPWidget?: {
      version: string;
      initWidget: typeof initWidget;
      stylesInjected: boolean;
      scriptInitialized: boolean;
    };
  }
}

/**
 * Inject widget styles into the document (once per page)
 */
function injectStyles(): void {
  // Use hash-based style ID for cache busting
  const styleId = `tp-widget-styles-${STYLES_HASH}`;

  // Check if this version is already injected
  // Use querySelector instead of getElementById for reliability across environments
  if (document.querySelector(`#${styleId}`)) {
    return;
  }

  // Remove any old versions of the styles
  const oldStyles = document.querySelectorAll('[id^="tp-widget-styles"]');
  oldStyles.forEach(el => el.remove());

  // Inject new styles
  const styleElement = document.createElement('style');
  styleElement.id = styleId;
  styleElement.textContent = WIDGET_STYLES;
  document.head.appendChild(styleElement);

  if (window.__TPWidget) {
    window.__TPWidget.stylesInjected = true;
  }
}

/**
 * Initialize the widget runtime on window (Phase 0 singleton)
 */
function initRuntime(): void {
  if (!window.__TPWidget) {
    window.__TPWidget = {
      version: VERSION,
      initWidget,
      stylesInjected: false,
      scriptInitialized: false,
    };
  }
}

/**
 * Auto-initialize all widgets on the page
 */
function autoInit(): void {
  initRuntime();
  injectStyles();

  // Find all widget containers and initialize them
  const containers = document.querySelectorAll('[data-tp-widget]');
  containers.forEach((container) => {
    if (container instanceof HTMLElement && !container.dataset.tpInitialized) {
      initWidget(container);
      container.dataset.tpInitialized = 'true';
    }
  });
}

// Only set up event listeners and observers once, even if script loads multiple times
if (!window.__TPWidget?.scriptInitialized) {
  // Mark as initialized early to prevent race conditions
  initRuntime();
  if (window.__TPWidget) {
    window.__TPWidget.scriptInitialized = true;
  }

  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }

  // Watch for new widgets being added to the page (for Jupyter dynamic cell rendering)
  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof HTMLElement) {
            // Check if this node is a widget container
            if (node.matches('[data-tp-widget]') && !node.dataset.tpInitialized) {
              initRuntime();
              injectStyles();
              initWidget(node);
              node.dataset.tpInitialized = 'true';
            }
            // Check if this node contains widget containers
            const widgets = node.querySelectorAll('[data-tp-widget]');
            widgets.forEach((widget) => {
              if (widget instanceof HTMLElement && !widget.dataset.tpInitialized) {
                initRuntime();
                injectStyles();
                initWidget(widget);
                widget.dataset.tpInitialized = 'true';
              }
            });
          }
        });
      });
    });

    // Observe the entire document body for new widgets
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }
} else {
  // Script already initialized, just process any new widgets on the page
  autoInit();
}

// Export for manual initialization
export { initWidget, injectStyles, initRuntime };
