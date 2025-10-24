/**
 * StructuredPromptDiffView Component
 *
 * Displays a tree-based diff of StructuredPrompt structures.
 * Non-interactive for now - just displays the diff.
 */

import type { Component } from './base';
import type { StructuredPromptDiffData, NodeDelta, TextEdit } from '../diff-types';

/**
 * StructuredPromptDiffView component interface
 * Currently just the base Component interface
 */
export type StructuredPromptDiffView = Component;

/**
 * Build a StructuredPromptDiffView component from diff data
 */
export function buildStructuredPromptDiffView(
  data: StructuredPromptDiffData
): StructuredPromptDiffView {
  // 1. Create root element
  const element = document.createElement('div');
  element.className = 'tp-diff-view';
  element.setAttribute('data-role', 'tp-diff-structured');

  // 2. Build header
  const header = document.createElement('div');
  header.className = 'tp-diff-header';
  header.textContent = 'Structured prompt diff';
  element.appendChild(header);

  // 3. Build summary with stats
  const summary = document.createElement('div');
  summary.className = 'tp-diff-summary';

  const summaryItems: Array<{ label: string; value: string }> = [
    { label: 'Added', value: String(data.stats.nodes_added) },
    { label: 'Removed', value: String(data.stats.nodes_removed) },
    { label: 'Modified', value: String(data.stats.nodes_modified) },
    { label: 'Moved', value: String(data.stats.nodes_moved) },
    { label: 'Δ+', value: String(data.stats.text_added) },
    { label: 'Δ-', value: String(data.stats.text_removed) },
    { label: 'Edit volume', value: formatDecimal(data.metrics.struct_edit_count, 1) },
    { label: 'Span chars', value: String(data.metrics.struct_span_chars) },
    { label: 'Span %', value: formatPercent(data.metrics.struct_char_ratio) },
    { label: 'Order', value: formatDecimal(data.metrics.struct_order_score, 2) },
  ];

  for (const { label, value } of summaryItems) {
    const pill = document.createElement('span');
    pill.className = 'tp-diff-pill';
    pill.textContent = `${label}: ${value}`;
    summary.appendChild(pill);
  }

  element.appendChild(summary);

  // 4. Build body with diff tree
  const body = document.createElement('div');
  body.className = 'tp-diff-body';

  const tree = document.createElement('ul');
  tree.className = 'tp-diff-tree';
  tree.appendChild(renderNodeDelta(data.root));

  body.appendChild(tree);
  element.appendChild(body);

  // 5. Return component
  return {
    element,
    destroy: (): void => {
      // No cleanup needed for now
    },
  };
}

/**
 * Render a single NodeDelta as HTML
 */
function renderNodeDelta(delta: NodeDelta): HTMLElement {
  const li = document.createElement('li');
  li.className = 'tp-diff-node';
  li.setAttribute('data-status', delta.status);

  // Node title
  const title = document.createElement('div');
  title.className = 'tp-diff-node-title';
  title.textContent = `${delta.element_type} · ${formatNodeKey(delta.key)}`;
  li.appendChild(title);

  // Metadata
  const meta: string[] = [];

  if (delta.before_index !== null || delta.after_index !== null) {
    const beforeIdx = delta.before_index !== null ? String(delta.before_index) : '';
    const afterIdx = delta.after_index !== null ? String(delta.after_index) : '';
    meta.push(`idx: ${beforeIdx} → ${afterIdx}`);
  }

  if (Object.keys(delta.attr_changes).length > 0) {
    const fields = Object.keys(delta.attr_changes).sort().join(', ');
    meta.push(`fields: ${fields}`);
  }

  if (meta.length > 0) {
    const metaDiv = document.createElement('div');
    metaDiv.className = 'tp-diff-node-meta';
    metaDiv.textContent = meta.join(' · ');
    li.appendChild(metaDiv);
  }

  // Text edits
  if (delta.text_edits.length > 0) {
    const editsDiv = document.createElement('div');
    for (const edit of delta.text_edits) {
      editsDiv.appendChild(renderTextEdit(edit));
    }
    li.appendChild(editsDiv);
  }

  // Children
  if (delta.children.length > 0) {
    const childTree = document.createElement('ul');
    childTree.className = 'tp-diff-tree';
    for (const child of delta.children) {
      childTree.appendChild(renderNodeDelta(child));
    }
    li.appendChild(childTree);
  }

  return li;
}

/**
 * Render a TextEdit as HTML
 */
function renderTextEdit(edit: TextEdit): HTMLElement {
  const span = document.createElement('span');
  span.className = 'tp-diff-text';

  if (edit.op === 'equal') {
    span.textContent = edit.after;
  } else if (edit.op === 'insert') {
    span.classList.add('tp-diff-ins');
    span.textContent = `+ ${edit.after}`;
  } else if (edit.op === 'delete') {
    span.classList.add('tp-diff-del');
    span.textContent = `- ${edit.before}`;
  } else {
    // replace
    const delSpan = document.createElement('span');
    delSpan.className = 'tp-diff-del';
    delSpan.textContent = `- ${edit.before}`;

    const insSpan = document.createElement('span');
    insSpan.className = 'tp-diff-ins';
    insSpan.textContent = `+ ${edit.after}`;

    span.appendChild(delSpan);
    span.appendChild(document.createTextNode(' '));
    span.appendChild(insSpan);
  }

  return span;
}

function formatNodeKey(key: NodeDelta['key']): string {
  if (key === null || key === undefined) {
    return 'None';
  }
  return String(key);
}

function formatDecimal(value: number, fractionDigits: number): string {
  if (!Number.isFinite(value)) {
    if (fractionDigits <= 0) {
      return '0';
    }
    return `0.${'0'.repeat(fractionDigits)}`;
  }
  return value.toFixed(fractionDigits);
}

function formatPercent(value: number, fractionDigits = 1): string {
  if (!Number.isFinite(value)) {
    return '0%';
  }
  const clamped = Math.min(Math.max(value, 0), 1);
  return `${(clamped * 100).toFixed(fractionDigits)}%`;
}
