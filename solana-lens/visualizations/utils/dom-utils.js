/**
 * DOM Utility Functions
 * 
 * Helper functions for working with the DOM
 */

/**
 * Load a CSS stylesheet
 * @param {string} url - URL of the stylesheet
 * @returns {HTMLElement} - The created link element
 */
export function loadStyleSheet(url) {
  // Check if stylesheet is already loaded
  const existingLinks = document.querySelectorAll('link[rel="stylesheet"]');
  for (const link of existingLinks) {
    if (link.href.endsWith(url)) {
      return link;
    }
  }
  
  // Create and append new stylesheet link
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = url;
  document.head.appendChild(link);
  return link;
}

/**
 * Create an element with attributes and children
 * @param {string} tagName - The tag name of the element to create
 * @param {Object} attributes - Attributes to set on the element
 * @param {Array|string|HTMLElement} children - Child elements or text content
 * @returns {HTMLElement} - The created element
 */
export function createElement(tagName, attributes = {}, children = []) {
  const element = document.createElement(tagName);
  
  // Set attributes
  for (const [key, value] of Object.entries(attributes)) {
    if (key === 'style' && typeof value === 'object') {
      Object.assign(element.style, value);
    } else if (key.startsWith('on') && typeof value === 'function') {
      // Event handlers
      const eventName = key.substring(2).toLowerCase();
      element.addEventListener(eventName, value);
    } else {
      element.setAttribute(key, value);
    }
  }
  
  // Add children
  if (Array.isArray(children)) {
    children.forEach(child => {
      if (child instanceof HTMLElement) {
        element.appendChild(child);
      } else if (child !== null && child !== undefined) {
        element.appendChild(document.createTextNode(String(child)));
      }
    });
  } else if (children instanceof HTMLElement) {
    element.appendChild(children);
  } else if (children !== null && children !== undefined) {
    element.textContent = String(children);
  }
  
  return element;
}

/**
 * Create a gallery of visualization thumbnails
 * @param {Array} visualizations - Array of visualization objects
 * @param {HTMLElement} container - Container element
 * @param {Function} onSelect - Callback function when a visualization is selected
 */
export function createVisualizationGallery(visualizations, container, onSelect) {
  const gallery = createElement('div', { class: 'visualization-gallery' });
  
  visualizations.forEach(viz => {
    const card = createElement('div', { 
      class: 'visualization-card',
      style: { cursor: 'pointer' },
      onclick: () => onSelect(viz.id)
    }, [
      createElement('div', { class: 'viz-thumbnail' }, [
        createElement('img', { 
          src: viz.thumbnail || 'assets/images/default-thumbnail.png',
          alt: viz.name
        })
      ]),
      createElement('div', { class: 'viz-info' }, [
        createElement('h3', {}, viz.name),
        createElement('p', { class: 'viz-description' }, viz.description),
        createElement('div', { class: 'viz-tags' }, viz.tags.map(tag => 
          createElement('span', { class: 'viz-tag' }, tag)
        ))
      ])
    ]);
    
    gallery.appendChild(card);
  });
  
  container.appendChild(gallery);
  return gallery;
}
