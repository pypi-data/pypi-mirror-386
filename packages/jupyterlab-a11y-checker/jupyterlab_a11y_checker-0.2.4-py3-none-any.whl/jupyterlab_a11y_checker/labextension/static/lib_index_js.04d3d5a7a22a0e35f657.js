"use strict";
(self["webpackChunkjupyterlab_a11y_checker"] = self["webpackChunkjupyterlab_a11y_checker"] || []).push([["lib_index_js"],{

/***/ "./lib/components/fix/base.js":
/*!************************************!*\
  !*** ./lib/components/fix/base.js ***!
  \************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   ButtonFixWidget: () => (/* binding */ ButtonFixWidget),
/* harmony export */   DropdownFixWidget: () => (/* binding */ DropdownFixWidget),
/* harmony export */   TextFieldFixWidget: () => (/* binding */ TextFieldFixWidget)
/* harmony export */ });
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _utils_detection_base__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../utils/detection/base */ "./lib/utils/detection/base.js");


// Intentionally keep base free of category-specific analysis. Widgets can override.
class FixWidget extends _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.Widget {
    constructor(issue, cell, aiEnabled) {
        super();
        this.currentPath = '';
        this.issue = issue;
        this.cell = cell;
        this.aiEnabled = aiEnabled;
        this.addClass('a11y-fix-widget');
    }
    // Method to remove the widget from the DOM
    removeIssueWidget() {
        const issueWidget = this.node.closest('.issue-widget');
        if (issueWidget) {
            const category = issueWidget.closest('.category');
            issueWidget.remove();
            if (category && !category.querySelector('.issue-widget')) {
                category.remove();
            }
        }
        // For all fixes, highlight the current cell
        this.cell.node.style.transition = 'background-color 0.5s ease';
        this.cell.node.style.backgroundColor = 'var(--success-green)';
        setTimeout(() => {
            this.cell.node.style.backgroundColor = '';
        }, 1000);
    }
    // Re-run content-based detectors for this cell only and dispatch an update
    async reanalyzeCellAndDispatch() {
        var _a, _b, _c;
        const notebookPanel = (_a = this.cell.parent) === null || _a === void 0 ? void 0 : _a.parent;
        if (!notebookPanel) {
            return;
        }
        // Find cell index within the notebook (TODO: Include cellIndex at the first place)
        const cellIndex = (_c = (_b = this.cell.parent) === null || _b === void 0 ? void 0 : _b.widgets.indexOf(this.cell)) !== null && _c !== void 0 ? _c : -1;
        if (cellIndex < 0) {
            return;
        }
        setTimeout(async () => {
            const issues = await (0,_utils_detection_base__WEBPACK_IMPORTED_MODULE_1__.analyzeCellIssues)(notebookPanel, cellIndex);
            const event = new CustomEvent('notebookReanalyzed', {
                detail: { issues, isCellUpdate: true },
                bubbles: true,
                composed: true
            });
            // Dispatch from this widget's node so it bubbles up to the main panel
            //this.node.dispatchEvent(event);
            // Also dispatch directly on the main panel root for robustness
            const mainPanelEl = document.getElementById('a11y-sidebar');
            if (mainPanelEl) {
                mainPanelEl.dispatchEvent(event);
            }
        }, 100);
    }
    // Generic notebook reanalysis hook. By default, just reanalyze this cell.
    // Widgets with notebook-wide effects (e.g., headings) should override.
    async reanalyzeNotebookAndDispatch() {
        await this.reanalyzeCellAndDispatch();
    }
}
class ButtonFixWidget extends FixWidget {
    constructor(issue, cell, aiEnabled) {
        super(issue, cell, aiEnabled);
        this.node.innerHTML = `
      <div class="fix-description">${this.getDescription()}</div>
      <div class="button-container">
        <button class="jp-Button2 button-fix-button">
          <span class="material-icons">check</span>
          <div>${this.getApplyButtonText()}</div>
        </button>
      </div>
    `;
        this.applyButton = this.node.querySelector('.button-fix-button');
        this.applyButton.addEventListener('click', () => this.applyFix());
    }
}
class TextFieldFixWidget extends FixWidget {
    constructor(issue, cell, aiEnabled) {
        super(issue, cell, aiEnabled);
        // Simplified DOM structure
        this.node.innerHTML = `
        <div class="fix-description">${this.getDescription()}</div>
        <div class="textfield-fix-widget">
          <input type="text" class="jp-a11y-input" placeholder="Input text here...">
          <div class="textfield-buttons">
              <button class="jp-Button2 suggest-button">
                  <span class="material-icons">auto_awesome</span>
                  <div>Get AI Suggestions</div>
              </button>
              <button class="jp-Button2 apply-button">
                  <span class="material-icons">check</span>
                  <div>Apply</div>
              </button>
          </div>
        </div>
      `;
        // Apply Button
        const applyButton = this.node.querySelector('.apply-button');
        if (applyButton) {
            applyButton.addEventListener('click', () => {
                const textInput = this.node.querySelector('.jp-a11y-input');
                this.applyTextToCell(textInput.value.trim());
            });
        }
        // Suggest Button
        const suggestButton = this.node.querySelector('.suggest-button');
        suggestButton.style.display = aiEnabled ? 'flex' : 'none';
        suggestButton.addEventListener('click', () => this.displayAISuggestions());
        // Textfield Value
        const textFieldValue = this.node.querySelector('.jp-a11y-input');
        if (this.issue.suggestedFix) {
            textFieldValue.value = this.issue.suggestedFix;
        }
    }
}
class DropdownFixWidget extends FixWidget {
    constructor(issue, cell, aiEnabled) {
        super(issue, cell, aiEnabled);
        this.selectedOption = '';
        // Simplified DOM structure with customizable text
        this.node.innerHTML = `
      <div class="fix-description">${this.getDescription()}</div>
      <div class="dropdown-fix-widget">
        <div class="custom-dropdown">
          <button class="dropdown-button">
            <span class="dropdown-text"></span>
            <svg class="dropdown-arrow" viewBox="0 0 24 24" width="24" height="24">
              <path fill="currentColor" d="M7 10l5 5 5-5z"/>
            </svg>
          </button>
          <div class="dropdown-content hidden">
          </div>
        </div>
        <button class="jp-Button2 apply-button" style="${this.shouldShowApplyButton() ? '' : 'display: none;'}">
          <span class="material-icons">check</span>
          <div>Apply</div>
        </button>
      </div>
    `;
        this.dropdownButton = this.node.querySelector('.dropdown-button');
        this.dropdownContent = this.node.querySelector('.dropdown-content');
        this.dropdownText = this.node.querySelector('.dropdown-text');
        this.applyButton = this.node.querySelector('.apply-button');
        // Set initial text
        if (this.dropdownText) {
            this.dropdownText.textContent = this.getDefaultDropdownText();
        }
        // Populate dropdown options
        if (this.dropdownContent) {
            this.dropdownContent.innerHTML = this.getDropdownOptions();
        }
        // Setup dropdown handlers
        this.setupDropdownHandlers();
    }
    setupDropdownHandlers() {
        // Toggle dropdown
        this.dropdownButton.addEventListener('click', e => {
            e.stopPropagation(); // Prevent event from bubbling up
            this.dropdownContent.classList.toggle('hidden');
            this.dropdownButton.classList.toggle('active');
        });
        // Close dropdown when clicking outside
        document.addEventListener('click', event => {
            if (!this.node.contains(event.target)) {
                this.dropdownContent.classList.add('hidden');
                this.dropdownButton.classList.remove('active');
            }
        });
        // Option selection
        const options = this.dropdownContent.querySelectorAll('.dropdown-option');
        options.forEach(option => {
            option.addEventListener('click', e => {
                var _a;
                e.stopPropagation(); // Prevent event from bubbling up
                const value = option.dataset.value || '';
                this.selectedOption = value;
                this.handleOptionSelect(value);
                this.dropdownText.textContent =
                    ((_a = option.textContent) === null || _a === void 0 ? void 0 : _a.trim()) || '';
                this.dropdownContent.classList.add('hidden');
                this.dropdownButton.classList.remove('active');
                if (this.shouldShowApplyButton()) {
                    this.applyButton.style.display = 'flex';
                }
            });
        });
        // Apply button
        this.applyButton.addEventListener('click', () => {
            if (this.selectedOption) {
                this.applyDropdownSelection(this.selectedOption);
            }
        });
    }
}


/***/ }),

/***/ "./lib/components/fix/buttonFixes.js":
/*!*******************************************!*\
  !*** ./lib/components/fix/buttonFixes.js ***!
  \*******************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   TableScopeFixWidget: () => (/* binding */ TableScopeFixWidget)
/* harmony export */ });
/* harmony import */ var _base__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./base */ "./lib/components/fix/base.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../utils */ "./lib/utils/edit.js");
// In src/components/fix/buttonFixes.ts


class TableScopeFixWidget extends _base__WEBPACK_IMPORTED_MODULE_0__.ButtonFixWidget {
    getDescription() {
        return 'Add scope attributes to all table headers:';
    }
    getApplyButtonText() {
        return 'Apply Scope Fixes';
    }
    async applyFix() {
        const entireCellContent = this.cell.model.sharedModel.getSource();
        //console.log('Processing table for scope fix:', target);
        // Process the table
        const processTable = (tableHtml) => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(tableHtml, 'text/html');
            const table = doc.querySelector('table');
            if (!table) {
                return tableHtml;
            }
            // Get all rows, handling both direct tr children and tr children of tbody
            const rows = Array.from(table.querySelectorAll('tr'));
            //console.log('Found rows:', rows.length);
            if (rows.length === 0) {
                //console.log('No rows found in table');
                return tableHtml;
            }
            // Create new table structure
            const newTable = doc.createElement('table');
            // Copy all attributes from original table
            Array.from(table.attributes).forEach(attr => {
                newTable.setAttribute(attr.name, attr.value);
            });
            // Copy caption if it exists
            const existingCaption = table.querySelector('caption');
            if (existingCaption) {
                //console.log('Found existing caption:', existingCaption.textContent);
                newTable.appendChild(existingCaption.cloneNode(true));
            }
            // Process header row
            const headerRow = rows[0];
            const headerCells = headerRow.querySelectorAll('th, td');
            //console.log('Header cells found:', headerCells.length);
            if (headerCells.length > 0) {
                const thead = doc.createElement('thead');
                const newHeaderRow = doc.createElement('tr');
                headerCells.forEach(cell => {
                    // Convert td to th if it's in the header row
                    const newCell = doc.createElement('th');
                    newCell.innerHTML = cell.innerHTML;
                    newCell.setAttribute('scope', 'col');
                    newHeaderRow.appendChild(newCell);
                });
                thead.appendChild(newHeaderRow);
                newTable.appendChild(thead);
            }
            // Process remaining rows
            const tbody = doc.createElement('tbody');
            rows.slice(1).forEach(row => {
                const newRow = doc.createElement('tr');
                const cells = row.querySelectorAll('td, th');
                cells.forEach((cell, index) => {
                    const newCell = cell.cloneNode(true);
                    if (cell.tagName.toLowerCase() === 'th') {
                        newCell.setAttribute('scope', 'row');
                    }
                    newRow.appendChild(newCell);
                });
                tbody.appendChild(newRow);
            });
            newTable.appendChild(tbody);
            // Format the table HTML with proper indentation
            const formatTable = (table) => {
                const indent = '  '; // 2 spaces for indentation
                let result = '<table';
                // Add attributes
                Array.from(table.attributes).forEach(attr => {
                    result += ` ${attr.name}="${attr.value}"`;
                });
                result += '>\n';
                // Add caption if it exists
                const caption = table.querySelector('caption');
                if (caption) {
                    result += `${indent}<caption>${caption.textContent}</caption>\n`;
                }
                // Add thead if it exists
                const thead = table.querySelector('thead');
                if (thead) {
                    result += `${indent}<thead>\n`;
                    const headerRow = thead.querySelector('tr');
                    if (headerRow) {
                        result += `${indent}${indent}<tr>\n`;
                        Array.from(headerRow.children).forEach(cell => {
                            result += `${indent}${indent}${indent}${cell.outerHTML}\n`;
                        });
                        result += `${indent}${indent}</tr>\n`;
                    }
                    result += `${indent}</thead>\n`;
                }
                // Add tbody
                const tbody = table.querySelector('tbody');
                if (tbody) {
                    result += `${indent}<tbody>\n`;
                    Array.from(tbody.children).forEach(row => {
                        result += `${indent}${indent}<tr>\n`;
                        Array.from(row.children).forEach(cell => {
                            result += `${indent}${indent}${indent}${cell.outerHTML}\n`;
                        });
                        result += `${indent}${indent}</tr>\n`;
                    });
                    result += `${indent}</tbody>\n`;
                }
                result += '</table>';
                return result;
            };
            const result = formatTable(newTable);
            return result;
        };
        // Prefer precise slice replacement using detector-provided offsets
        const offsets = (0,_utils__WEBPACK_IMPORTED_MODULE_1__.getIssueOffsets)(this.issue, entireCellContent.length);
        if (offsets) {
            const { offsetStart, offsetEnd } = offsets;
            const originalSlice = entireCellContent.slice(offsetStart, offsetEnd);
            const replacedSlice = processTable(originalSlice);
            const newContent = (0,_utils__WEBPACK_IMPORTED_MODULE_1__.replaceSlice)(entireCellContent, offsetStart, offsetEnd, replacedSlice);
            this.cell.model.sharedModel.setSource(newContent);
        }
        else {
            // Fallback: find and replace first table occurrence
            const tableRegex = /<table[^>]*>[\s\S]*?<\/table>/;
            const match = entireCellContent.match(tableRegex);
            if (match) {
                const newContent = entireCellContent.replace(match[0], processTable(match[0]));
                this.cell.model.sharedModel.setSource(newContent);
            }
        }
        await this.reanalyzeCellAndDispatch();
        this.removeIssueWidget();
    }
}


/***/ }),

/***/ "./lib/components/fix/dropdownFixes.js":
/*!*********************************************!*\
  !*** ./lib/components/fix/dropdownFixes.js ***!
  \*********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   HeadingOrderFixWidget: () => (/* binding */ HeadingOrderFixWidget),
/* harmony export */   TableHeaderFixWidget: () => (/* binding */ TableHeaderFixWidget)
/* harmony export */ });
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../../utils */ "./lib/utils/edit.js");
/* harmony import */ var _utils_detection_category_table__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../utils/detection/category/table */ "./lib/utils/detection/category/table.js");
/* harmony import */ var _base__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./base */ "./lib/components/fix/base.js");
/* harmony import */ var _utils_detection_category_heading__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../utils/detection/category/heading */ "./lib/utils/detection/category/heading.js");

// Keep imports minimal; reanalysis now handled by base class helpers

// import { NotebookPanel } from '@jupyterlab/notebook';


class TableHeaderFixWidget extends _base__WEBPACK_IMPORTED_MODULE_2__.DropdownFixWidget {
    getDescription() {
        return 'Choose which row or column should be used as the header:';
    }
    constructor(issue, cell, aiEnabled) {
        super(issue, cell, aiEnabled);
    }
    getDefaultDropdownText() {
        return 'Select header type';
    }
    getDropdownOptions() {
        return `
        <div class="dropdown-option" data-value="first-row">
          The first row is a header
        </div>
        <div class="dropdown-option" data-value="first-column">
          The first column is a header
        </div>
        <div class="dropdown-option" data-value="both">
          The first row and column are headers
        </div>
      `;
    }
    shouldShowApplyButton() {
        return true;
    }
    handleOptionSelect(value) {
        var _a, _b;
        this.dropdownText.textContent =
            ((_b = (_a = this.dropdownContent
                .querySelector(`[data-value="${value}"]`)) === null || _a === void 0 ? void 0 : _a.textContent) === null || _b === void 0 ? void 0 : _b.trim()) || 'Select header type';
    }
    applyDropdownSelection(headerType) {
        const entireCellContent = this.cell.model.sharedModel.getSource();
        const target = this.issue.issueContentRaw;
        const convertToHeaderCell = (cell) => {
            // Remove any existing th tags if present
            cell = cell.replace(/<\/?th[^>]*>/g, '');
            // Remove td tags if present
            cell = cell.replace(/<\/?td[^>]*>/g, '');
            // Wrap with th tags
            return `<th>${cell.trim()}</th>`;
        };
        const processTable = (tableHtml) => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(tableHtml, 'text/html');
            const table = doc.querySelector('table');
            if (!table) {
                return tableHtml;
            }
            // Get all rows, filtering out empty ones
            const rows = Array.from(table.querySelectorAll('tr')).filter(row => row.querySelectorAll('td, th').length > 0);
            if (rows.length === 0) {
                return tableHtml;
            }
            switch (headerType) {
                case 'first-row': {
                    // Convert first row cells to headers
                    const firstRow = rows[0];
                    const cells = Array.from(firstRow.querySelectorAll('td, th'));
                    cells.forEach(cell => {
                        const newHeader = convertToHeaderCell(cell.innerHTML);
                        cell.outerHTML = newHeader;
                    });
                    break;
                }
                case 'first-column': {
                    // Convert first column cells to headers
                    rows.forEach(row => {
                        const firstCell = row.querySelector('td, th');
                        if (firstCell) {
                            const newHeader = convertToHeaderCell(firstCell.innerHTML);
                            firstCell.outerHTML = newHeader;
                        }
                    });
                    break;
                }
                case 'both': {
                    // Convert both first row and first column
                    rows.forEach((row, rowIndex) => {
                        const cells = Array.from(row.querySelectorAll('td, th'));
                        cells.forEach((cell, cellIndex) => {
                            if (rowIndex === 0 || cellIndex === 0) {
                                const newHeader = convertToHeaderCell(cell.innerHTML);
                                cell.outerHTML = newHeader;
                            }
                        });
                    });
                    break;
                }
            }
            return table.outerHTML;
        };
        const newContent = entireCellContent.replace(target, processTable(target));
        this.cell.model.sharedModel.setSource(newContent);
        this.removeIssueWidget();
        // Wait a short delay for the cell to update
        setTimeout(async () => {
            var _a, _b;
            if ((_a = this.cell.parent) === null || _a === void 0 ? void 0 : _a.parent) {
                try {
                    // Only analyze table issues
                    const tableIssues = await (0,_utils_detection_category_table__WEBPACK_IMPORTED_MODULE_1__.analyzeTableIssues)(this.cell.parent.parent);
                    // Find the main panel widget
                    const mainPanel = (_b = document
                        .querySelector('.a11y-panel')) === null || _b === void 0 ? void 0 : _b.closest('.lm-Widget');
                    if (mainPanel) {
                        // Dispatch a custom event with just table issues
                        const event = new CustomEvent('notebookReanalyzed', {
                            detail: {
                                issues: tableIssues,
                                isTableUpdate: true
                            },
                            bubbles: true
                        });
                        mainPanel.dispatchEvent(event);
                    }
                }
                catch (error) {
                    console.error('Error reanalyzing notebook:', error);
                }
            }
        }, 100); // Small delay to ensure cell content is updated
    }
}
class HeadingOrderFixWidget extends _base__WEBPACK_IMPORTED_MODULE_2__.DropdownFixWidget {
    getDescription() {
        return 'Choose from one of the following heading styles instead:';
    }
    // private notebookPanel: NotebookPanel;
    constructor(issue, cell, aiEnabled) {
        super(issue, cell, aiEnabled);
        this._currentLevel = 1; // Initialize with default value
        // Get reference to notebook panel
        // Keep reference in case other methods require it; not used in reanalysis anymore
        // this.notebookPanel = cell.parent?.parent as NotebookPanel;
        // Parse and set the current level immediately
        this._currentLevel = HeadingOrderFixWidget.parseHeadingLevel(issue.issueContentRaw);
        // Initialize values after super
        this.initializeValues(issue);
        // Setup apply button handler
        if (this.applyButton) {
            this.applyButton.addEventListener('click', async () => {
                if (this.selectedLevel) {
                    this.applyDropdownSelection(`h${this.selectedLevel}`);
                    await this.reanalyzeNotebookAndDispatch();
                }
            });
        }
    }
    shouldShowApplyButton() {
        return true;
    }
    getDefaultDropdownText() {
        return `Current: h${this._currentLevel}`;
    }
    getDropdownOptions() {
        return ''; // Options are set in constructor after initialization
    }
    handleOptionSelect(value) {
        const level = parseInt(value.replace('h', ''));
        this.selectedLevel = level;
        this.dropdownText.textContent = `Change to h${level}`;
        // Hide the dropdown content
        if (this.dropdownContent) {
            this.dropdownContent.classList.add('hidden');
            this.dropdownButton.classList.remove('active');
        }
        // Show the apply button
        if (this.applyButton) {
            this.applyButton.style.display = 'flex';
        }
    }
    applyDropdownSelection(selectedValue) {
        var _a, _b;
        if (!this.selectedLevel) {
            return;
        }
        const entireCellContent = this.cell.model.sharedModel.getSource();
        const target = this.issue.issueContentRaw;
        let newContent = entireCellContent;
        const offsets = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getIssueOffsets)(this.issue, entireCellContent.length);
        if (offsets) {
            const { offsetStart, offsetEnd } = offsets;
            const originalSlice = entireCellContent.slice(offsetStart, offsetEnd);
            let replacedSlice = originalSlice;
            // Markdown heading: starts with hashes (allow missing or multiple spaces)
            const mdMatch = originalSlice.match(/^(#{1,6})[ \t]*(.*)$/m);
            if (mdMatch) {
                const headingText = (mdMatch[2] || '').trim();
                const trailingNewline = originalSlice.endsWith('\n') ? '\n' : '';
                replacedSlice = `${'#'.repeat(this.selectedLevel)} ${headingText}${trailingNewline}`;
            }
            else {
                // HTML heading
                const inner = ((_a = originalSlice.match(/<h\d[^>]*>([\s\S]*?)<\/h\d>/i)) === null || _a === void 0 ? void 0 : _a[1]) || '';
                replacedSlice = `<h${this.selectedLevel}>${inner}</h${this.selectedLevel}>`;
            }
            newContent = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.replaceSlice)(entireCellContent, offsetStart, offsetEnd, replacedSlice);
        }
        else {
            // Fallback: use previous behavior on entire cell
            if (entireCellContent.trim().startsWith('#')) {
                const currentLevelMatch = entireCellContent.match(/^(#+)[ \t]*/);
                if (currentLevelMatch) {
                    const currentMarkers = currentLevelMatch[1];
                    newContent = entireCellContent.replace(new RegExp(`^${currentMarkers}[ \\t]*(.*)$`, 'm'), `${'#'.repeat(this.selectedLevel)} $1`);
                }
            }
            else if (target.match(/<h\d[^>]*>/)) {
                newContent = entireCellContent.replace(target, `<h${this.selectedLevel}>${((_b = target.match(/<h\d[^>]*>([\s\S]*?)<\/h\d>/)) === null || _b === void 0 ? void 0 : _b[1]) || ''}</h${this.selectedLevel}>`);
            }
        }
        if (newContent !== entireCellContent) {
            this.cell.model.sharedModel.setSource(newContent);
            this.removeIssueWidget();
        }
    }
    initializeValues(issue) {
        var _a;
        // Get previous level from metadata
        this.previousLevel = (_a = issue.metadata) === null || _a === void 0 ? void 0 : _a.previousHeadingLevel;
        // If metadata doesn't have previous level, try to find the closest previous heading
        if (this.previousLevel === undefined) {
            this.previousLevel = this.findClosestPreviousHeading(issue.cellIndex);
        }
        // Update the dropdown text explicitly after initialization
        if (this.dropdownText) {
            this.dropdownText.textContent = this.getDefaultDropdownText();
        }
        // Force update dropdown content after initialization
        if (this.dropdownContent) {
            const validLevels = this.getValidHeadingLevels();
            this.dropdownContent.innerHTML = Array.from(validLevels)
                .sort((a, b) => a - b)
                .map(level => `
            <div class="dropdown-option" data-value="h${level}">
              Change to h${level}
            </div>
          `)
                .join('');
            // Add click handlers to the options
            const options = this.dropdownContent.querySelectorAll('.dropdown-option');
            options.forEach(option => {
                option.addEventListener('click', e => {
                    e.stopPropagation();
                    const value = option.dataset.value;
                    if (value) {
                        this.handleOptionSelect(value);
                    }
                });
            });
        }
    }
    // Static helper method to parse heading level
    static parseHeadingLevel(rawContent) {
        // Try HTML heading pattern first
        const htmlMatch = rawContent.match(/<h([1-6])[^>]*>/i);
        if (htmlMatch) {
            const level = parseInt(htmlMatch[1]);
            return level;
        }
        // Try Markdown heading pattern - match # followed by space
        const mdMatch = rawContent.match(/^(#{1,6})\s+/m);
        if (mdMatch) {
            const level = mdMatch[1].length;
            return level;
        }
        return 1; // Default level
    }
    findClosestPreviousHeading(cellIndex) {
        const notebook = this.cell.parent;
        if (!notebook) {
            return undefined;
        }
        // Start from the cell before the current one and go backwards
        for (let i = cellIndex - 1; i >= 0; i--) {
            const prevCell = notebook.widgets[i];
            if (!prevCell || prevCell.model.type !== 'markdown') {
                continue;
            }
            const content = prevCell.model.sharedModel.getSource();
            // Check for markdown heading (# syntax)
            const mdMatch = content.match(/^(#{1,6})\s+/m);
            if (mdMatch) {
                return mdMatch[1].length;
            }
            // Check for HTML heading
            const htmlMatch = content.match(/<h([1-6])[^>]*>/i);
            if (htmlMatch) {
                return parseInt(htmlMatch[1]);
            }
        }
        return undefined;
    }
    getValidHeadingLevels() {
        const validLevels = new Set();
        // Always add h2 as a valid option
        validLevels.add(2);
        if (this.previousLevel !== undefined) {
            // Special case: if previous heading is h1, current heading must be h2
            if (this.previousLevel === 1) {
                return validLevels;
            }
            // Can stay at the same level as the previous heading (but not if it's the current level)
            if (this.previousLevel !== this._currentLevel) {
                validLevels.add(this.previousLevel);
            }
            // Can go exactly one level deeper than the previous heading (but not if it's the current level)
            if (this.previousLevel < 6) {
                const nextLevel = this.previousLevel + 1;
                if (nextLevel !== this._currentLevel) {
                    validLevels.add(nextLevel);
                }
            }
            // Can go exactly one level higher than the previous heading (but not if it's the current level)
            if (this.previousLevel > 1) {
                const prevLevel = this.previousLevel - 1;
                if (prevLevel !== this._currentLevel && prevLevel > 1) {
                    // Also ensure we never include h1
                    validLevels.add(prevLevel);
                }
            }
        }
        return validLevels;
    }
    // Override notebook reanalysis to run heading-wide checks
    async reanalyzeNotebookAndDispatch() {
        var _a;
        const notebookPanel = (_a = this.cell.parent) === null || _a === void 0 ? void 0 : _a.parent;
        if (!notebookPanel) {
            return;
        }
        setTimeout(async () => {
            var _a;
            const headingHierarchyIssues = await (0,_utils_detection_category_heading__WEBPACK_IMPORTED_MODULE_3__.analyzeHeadingHierarchy)(notebookPanel);
            const headingOneIssues = await (0,_utils_detection_category_heading__WEBPACK_IMPORTED_MODULE_3__.detectHeadingOneIssue)('', 0, 'markdown', notebookPanel.content.widgets);
            const allHeadingIssues = [...headingHierarchyIssues, ...headingOneIssues];
            const mainPanel = (_a = document
                .querySelector('.a11y-panel')) === null || _a === void 0 ? void 0 : _a.closest('.lm-Widget');
            if (mainPanel) {
                const event = new CustomEvent('notebookReanalyzed', {
                    detail: {
                        issues: allHeadingIssues,
                        isHeadingUpdate: true
                    },
                    bubbles: true
                });
                mainPanel.dispatchEvent(event);
            }
        }, 100);
    }
}


/***/ }),

/***/ "./lib/components/fix/textfieldFixes.js":
/*!**********************************************!*\
  !*** ./lib/components/fix/textfieldFixes.js ***!
  \**********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   HeadingOneFixWidget: () => (/* binding */ HeadingOneFixWidget),
/* harmony export */   ImageAltFixWidget: () => (/* binding */ ImageAltFixWidget),
/* harmony export */   LinkTextFixWidget: () => (/* binding */ LinkTextFixWidget),
/* harmony export */   TableCaptionFixWidget: () => (/* binding */ TableCaptionFixWidget)
/* harmony export */ });
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../../utils */ "./lib/utils/edit.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../utils */ "./lib/utils/ai-utils.js");
/* harmony import */ var _base__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./base */ "./lib/components/fix/base.js");



class ImageAltFixWidget extends _base__WEBPACK_IMPORTED_MODULE_2__.TextFieldFixWidget {
    getDescription() {
        return 'Add or update alt text for the image:';
    }
    constructor(issue, cell, aiEnabled, visionSettings) {
        super(issue, cell, aiEnabled);
        this.visionSettings = visionSettings;
    }
    async applyTextToCell(providedAltText) {
        var _a, _b;
        if (providedAltText === '') {
            return;
        }
        const entireCellContent = this.cell.model.sharedModel.getSource();
        const target = this.issue.issueContentRaw;
        // Try to parse deterministic offsets from metadata.issueId (format: cell-{idx}-image-missing-alt-o{start}-{end})
        const offsets = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getIssueOffsets)(this.issue, entireCellContent.length);
        const offsetStart = (_a = offsets === null || offsets === void 0 ? void 0 : offsets.offsetStart) !== null && _a !== void 0 ? _a : null;
        const offsetEnd = (_b = offsets === null || offsets === void 0 ? void 0 : offsets.offsetEnd) !== null && _b !== void 0 ? _b : null;
        // Offsets are already validated in getIssueOffsets
        // Handle HTML image tags
        const handleHtmlImage = (imageText) => {
            // Alt attribute exists but is empty
            if (imageText.includes('alt=""') || imageText.includes("alt=''")) {
                return imageText.replace(/alt=["']\s*["']/, `alt="${providedAltText}"`);
            }
            // Alt attribute does not exist
            return imageText.replace(/\s*\/?>(?=$)/, ` alt="${providedAltText}"$&`);
        };
        // Handle markdown images
        const handleMarkdownImage = (imageText) => {
            return imageText.replace(/!\[\]/, `![${providedAltText}]`);
        };
        let newContent = entireCellContent;
        if (offsetStart !== null && offsetEnd !== null) {
            const originalSlice = entireCellContent.slice(offsetStart, offsetEnd);
            let replacedSlice = originalSlice;
            if (originalSlice.startsWith('<img')) {
                replacedSlice = handleHtmlImage(originalSlice);
            }
            else if (originalSlice.startsWith('![')) {
                replacedSlice = handleMarkdownImage(originalSlice);
            }
            newContent = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.replaceSlice)(entireCellContent, offsetStart, offsetEnd, replacedSlice);
        }
        else {
            // Fallback to previous behavior using the captured target
            if (target.startsWith('<img')) {
                newContent = entireCellContent.replace(target, handleHtmlImage(target));
            }
            else if (target.startsWith('![')) {
                newContent = entireCellContent.replace(target, handleMarkdownImage(target));
            }
        }
        this.cell.model.sharedModel.setSource(newContent);
        // Remove the issue widget
        this.removeIssueWidget();
        await this.reanalyzeCellAndDispatch();
    }
    async displayAISuggestions() {
        var _a;
        const altTextInput = this.node.querySelector('.jp-a11y-input');
        if (!altTextInput) {
            return;
        }
        // Save the original placeholder text
        const originalPlaceholder = altTextInput.placeholder;
        // Create loading overlay (so we can see the loading state)
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <span class="material-icons loading">refresh</span>
            Getting AI suggestions...
        `;
        // Add relative positioning to input container and append loading overlay
        const inputContainer = altTextInput.parentElement;
        if (inputContainer) {
            inputContainer.style.position = 'relative';
            inputContainer.appendChild(loadingOverlay);
        }
        // Show loading state in the input
        altTextInput.disabled = true;
        altTextInput.style.color = 'transparent'; // Hide input text while loading
        altTextInput.placeholder = ''; // Clear placeholder while showing loading overlay
        try {
            const suggestion = await (0,_utils__WEBPACK_IMPORTED_MODULE_1__.getImageAltSuggestion)(this.issue, ((_a = this.cell.node.querySelector('img')) === null || _a === void 0 ? void 0 : _a.src) || '', this.visionSettings);
            if (suggestion !== 'Error') {
                // Extract alt text from the suggestion, handling both single and double quotes
                const altMatch = suggestion.match(/alt=['"]([^'"]*)['"]/);
                if (altMatch && altMatch[1]) {
                    altTextInput.value = altMatch[1];
                }
                else {
                    altTextInput.value = suggestion; // Fallback to full suggestion if no alt text found
                }
            }
            else {
                altTextInput.placeholder =
                    'Error getting suggestions. Please try again.';
            }
        }
        catch (error) {
            console.error(error);
            altTextInput.placeholder = 'Error getting suggestions. Please try again.';
        }
        finally {
            altTextInput.disabled = false;
            altTextInput.style.color = ''; // Restore text color
            loadingOverlay.remove(); // Remove loading overlay
            if (altTextInput.value) {
                altTextInput.placeholder = originalPlaceholder;
            }
        }
    }
}
class TableCaptionFixWidget extends _base__WEBPACK_IMPORTED_MODULE_2__.TextFieldFixWidget {
    getDescription() {
        return 'Add or update the caption for the table:';
    }
    constructor(issue, cell, aiEnabled, languageSettings) {
        super(issue, cell, aiEnabled);
        this.languageSettings = languageSettings;
    }
    async applyTextToCell(providedCaption) {
        if (providedCaption === '') {
            return;
        }
        const entireCellContent = this.cell.model.sharedModel.getSource();
        const target = this.issue.issueContentRaw;
        const handleHtmlTable = (tableHtml) => {
            // Check if table already has a caption
            if (tableHtml.includes('<caption>')) {
                return tableHtml.replace(/<caption>.*?<\/caption>/, `<caption>${providedCaption}</caption>`);
            }
            else {
                return tableHtml.replace(/<table[^>]*>/, `$&\n  <caption>${providedCaption}</caption>`);
            }
        };
        let newContent = entireCellContent;
        if (target.includes('<table')) {
            const offsets = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getIssueOffsets)(this.issue, entireCellContent.length);
            if (offsets) {
                const { offsetStart, offsetEnd } = offsets;
                const originalSlice = entireCellContent.slice(offsetStart, offsetEnd);
                const replacedSlice = handleHtmlTable(originalSlice);
                newContent = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.replaceSlice)(entireCellContent, offsetStart, offsetEnd, replacedSlice);
            }
            else {
                // Fallback to previous behavior
                newContent = entireCellContent.replace(target, handleHtmlTable(target));
            }
        }
        this.cell.model.sharedModel.setSource(newContent);
        // Remove the issue widget
        this.removeIssueWidget();
        await this.reanalyzeCellAndDispatch();
    }
    async displayAISuggestions() {
        const captionInput = this.node.querySelector('.jp-a11y-input');
        if (!captionInput) {
            return;
        }
        // Save the original placeholder text
        const originalPlaceholder = captionInput.placeholder;
        // Create loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <span class="material-icons loading">refresh</span>
            Getting AI suggestions...
        `;
        // Add relative positioning to input container and append loading overlay
        const inputContainer = captionInput.parentElement;
        if (inputContainer) {
            inputContainer.style.position = 'relative';
            inputContainer.appendChild(loadingOverlay);
        }
        // Show loading state in the input
        captionInput.disabled = true;
        captionInput.style.color = 'transparent';
        captionInput.placeholder = '';
        try {
            const suggestion = await (0,_utils__WEBPACK_IMPORTED_MODULE_1__.getTableCaptionSuggestion)(this.issue, this.languageSettings);
            if (suggestion !== 'Error') {
                captionInput.value = suggestion;
            }
            else {
                captionInput.placeholder =
                    'Error getting suggestions. Please try again.';
            }
        }
        catch (error) {
            console.error(error);
            captionInput.placeholder = 'Error getting suggestions. Please try again.';
        }
        finally {
            captionInput.disabled = false;
            captionInput.style.color = '';
            loadingOverlay.remove();
            if (captionInput.value) {
                captionInput.placeholder = originalPlaceholder;
            }
        }
    }
}
class HeadingOneFixWidget extends _base__WEBPACK_IMPORTED_MODULE_2__.TextFieldFixWidget {
    getDescription() {
        return 'Add a new level one (h1) heading to the top of the notebook:';
    }
    constructor(issue, cell, aiEnabled) {
        super(issue, cell, aiEnabled);
        const input = this.node.querySelector('.jp-a11y-input');
        if (input) {
            input.placeholder = 'Input h1 heading text...';
        }
        // Always disable AI suggestion for missing H1 heading
        const suggestButton = this.node.querySelector('.suggest-button');
        if (suggestButton) {
            suggestButton.remove();
        }
    }
    removeIssueWidget() {
        var _a;
        const issueWidget = this.node.closest('.issue-widget');
        if (issueWidget) {
            const category = issueWidget.closest('.category');
            issueWidget.remove();
            if (category && !category.querySelector('.issue-widget')) {
                category.remove();
            }
        }
        // Highlight the first cell instead of the current cell
        const notebookPanel = (_a = this.cell.parent) === null || _a === void 0 ? void 0 : _a.parent;
        if (notebookPanel) {
            const firstCell = notebookPanel.content.widgets[0];
            if (firstCell) {
                firstCell.node.style.transition = 'background-color 0.5s ease';
                firstCell.node.style.backgroundColor = '#28A745';
                setTimeout(() => {
                    firstCell.node.style.backgroundColor = '';
                }, 1000);
            }
        }
    }
    applyTextToCell(providedHeading) {
        var _a, _b;
        if (providedHeading === '') {
            return;
        }
        // Get the notebook panel from the cell's parent hierarchy
        const notebookPanel = (_a = this.cell.parent) === null || _a === void 0 ? void 0 : _a.parent;
        if (!notebookPanel) {
            console.error('Could not find notebook panel');
            return;
        }
        // Create a new markdown cell with the h1 heading
        const newContent = `# ${providedHeading}`;
        // Insert a new cell at the top of the notebook
        const sharedModel = (_b = notebookPanel.content.model) === null || _b === void 0 ? void 0 : _b.sharedModel;
        if (sharedModel) {
            sharedModel.insertCell(0, {
                cell_type: 'markdown',
                source: newContent
            });
        }
        // Remove the issue widget
        this.removeIssueWidget();
    }
    async displayAISuggestions() {
        const headingInput = this.node.querySelector('.jp-a11y-input');
        if (!headingInput) {
            return;
        }
        // Save the original placeholder text
        const originalPlaceholder = headingInput.placeholder;
        // Create loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
        <span class="material-icons loading">refresh</span>
        Getting AI suggestions...
      `;
        // Add relative positioning to input container and append loading overlay
        const inputContainer = headingInput.parentElement;
        if (inputContainer) {
            inputContainer.style.position = 'relative';
            inputContainer.appendChild(loadingOverlay);
        }
        // Show loading state in the input
        headingInput.disabled = true;
        headingInput.style.color = 'transparent';
        headingInput.placeholder = '';
        try {
            // TODO: Implement AI suggestion??? Is it needed?
            headingInput.value = 'Notebook Title';
        }
        catch (error) {
            console.error(error);
            headingInput.placeholder = 'Error getting suggestions. Please try again.';
        }
        finally {
            headingInput.disabled = false;
            headingInput.style.color = '';
            loadingOverlay.remove();
            if (headingInput.value) {
                headingInput.placeholder = originalPlaceholder;
            }
        }
    }
}
class LinkTextFixWidget extends _base__WEBPACK_IMPORTED_MODULE_2__.TextFieldFixWidget {
    getDescription() {
        return 'Update the link text or aria-label:';
    }
    applyTextToCell(providedText) {
        var _a, _b;
        if (providedText === '') {
            return;
        }
        const entireCellContent = this.cell.model.sharedModel.getSource();
        const offsets = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getIssueOffsets)(this.issue, entireCellContent.length);
        const offsetStart = (_a = offsets === null || offsets === void 0 ? void 0 : offsets.offsetStart) !== null && _a !== void 0 ? _a : null;
        const offsetEnd = (_b = offsets === null || offsets === void 0 ? void 0 : offsets.offsetEnd) !== null && _b !== void 0 ? _b : null;
        let newContent = entireCellContent;
        const replaceMarkdownLinkText = (full) => {
            return full.replace(/\[[^\]]*\]/, `[${providedText}]`);
        };
        const replaceHtmlLinkTextOrAria = (full) => {
            if (/aria-label=/.test(full)) {
                return full.replace(/aria-label=["'].*?["']/i, `aria-label="${providedText}"`);
            }
            // If there is no aria-label and no visible inner text, add aria-label
            const innerText = (full.replace(/<a\b[^>]*>/i, '').replace(/<\/a>/i, '') || '')
                .replace(/<[^>]*>/g, '')
                .trim();
            if (innerText.length === 0) {
                return full.replace(/<a\b([^>]*)>/i, (_m, attrs) => `<a${attrs} aria-label="${providedText}">`);
            }
            // Otherwise, replace inner text
            return full.replace(/(<a\b[^>]*>)([\s\S]*?)(<\/a>)/i, (_m, pre, _inner, post) => `${pre}${providedText}${post}`);
        };
        if (offsetStart !== null && offsetEnd !== null) {
            const originalSlice = entireCellContent.slice(offsetStart, offsetEnd);
            let replacedSlice = originalSlice;
            if (originalSlice.trim().startsWith('<a')) {
                replacedSlice = replaceHtmlLinkTextOrAria(originalSlice);
            }
            else if (originalSlice.trim().startsWith('[')) {
                replacedSlice = replaceMarkdownLinkText(originalSlice);
            }
            newContent = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.replaceSlice)(entireCellContent, offsetStart, offsetEnd, replacedSlice);
        }
        else {
            const target = this.issue.issueContentRaw;
            if (target.trim().startsWith('<a')) {
                newContent = entireCellContent.replace(target, replaceHtmlLinkTextOrAria(target));
            }
            else if (target.trim().startsWith('[')) {
                newContent = entireCellContent.replace(target, replaceMarkdownLinkText(target));
            }
        }
        this.cell.model.sharedModel.setSource(newContent);
        this.removeIssueWidget();
        void this.reanalyzeCellAndDispatch();
    }
    async displayAISuggestions() {
        // Not implemented for links today
        return;
    }
}


/***/ }),

/***/ "./lib/components/issueWidget.js":
/*!***************************************!*\
  !*** ./lib/components/issueWidget.js ***!
  \***************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   CellIssueWidget: () => (/* binding */ CellIssueWidget)
/* harmony export */ });
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _fix__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./fix */ "./lib/components/fix/textfieldFixes.js");
/* harmony import */ var _fix__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./fix */ "./lib/components/fix/dropdownFixes.js");
/* harmony import */ var _fix__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./fix */ "./lib/components/fix/buttonFixes.js");
/* harmony import */ var _utils_metadata__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../utils/metadata */ "./lib/utils/metadata.js");



class CellIssueWidget extends _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.Widget {
    constructor(issue, cell, aiEnabled, mainPanel) {
        var _a;
        super();
        this.aiEnabled = false; // TODO: Create a higher order component to handle this
        this.issue = issue;
        this.cell = cell;
        this.aiEnabled = aiEnabled;
        this.mainPanel = mainPanel;
        const issueInformation = _utils_metadata__WEBPACK_IMPORTED_MODULE_4__.issueToDescription.get(issue.violationId);
        if (issue.customDescription) {
            issueInformation.description = issue.customDescription;
        }
        if (issue.customDetailedDescription) {
            issueInformation.detailedDescription = issue.customDetailedDescription;
        }
        this.addClass('issue-widget');
        // Tag widget with identifiers so the panel can selectively update
        this.node.setAttribute('data-cell-index', String(issue.cellIndex));
        this.node.setAttribute('data-violation-id', issue.violationId);
        this.node.innerHTML = `
      <button class="issue-header-button">
          <h3 class="issue-header"> ${(issueInformation === null || issueInformation === void 0 ? void 0 : issueInformation.title) || issue.violationId}</h3>
          <span class="chevron material-icons">expand_more</span>
      </button>
      <div class="collapsible-content" style="display: none;">
          <p class="description">
              ${issueInformation === null || issueInformation === void 0 ? void 0 : issueInformation.description}
          </p>
          <p class="detailed-description" style="display: none;">
              ${(issueInformation === null || issueInformation === void 0 ? void 0 : issueInformation.detailedDescription) || ''} (<a href="${(issueInformation === null || issueInformation === void 0 ? void 0 : issueInformation.descriptionUrl) || ''}" target="_blank">learn more about the issue and its impact</a>).
          </p>
          <div class="button-container">
              <button class="jp-Button2 locate-button">
                  <span class="material-icons">search</span>
                  <div>Locate</div>
              </button>
              <button class="jp-Button2 explain-button">
                  <span class="material-icons">question_mark</span>
                  <div>Learn more</div>
              </button>
          </div>
          <div class="offending-content-block">
              <div class="offending-title">Original content:</div>
              <pre class="offending-snippet" style="white-space: pre-wrap; max-height: 200px; overflow: auto; background: var(--jp-layout-color2); padding: 8px; border-radius: 4px; border: 1px solid var(--jp-border-color2);"></pre>
          </div>
          <div class="fix-widget-container"></div>
      </div>
    `;
        // Add event listeners using query selectors
        const headerButton = this.node.querySelector('.issue-header-button');
        const collapsibleContent = this.node.querySelector('.collapsible-content');
        // Toggle collapsible content when header is clicked
        headerButton === null || headerButton === void 0 ? void 0 : headerButton.addEventListener('click', () => {
            if (collapsibleContent) {
                const isHidden = collapsibleContent.style.display === 'none';
                collapsibleContent.style.display = isHidden ? 'block' : 'none';
                const expandIcon = this.node.querySelector('.chevron');
                expandIcon === null || expandIcon === void 0 ? void 0 : expandIcon.classList.toggle('expanded');
            }
        });
        const locateButton = this.node.querySelector('.locate-button');
        locateButton === null || locateButton === void 0 ? void 0 : locateButton.addEventListener('click', () => this.navigateToCell());
        const explainButton = this.node.querySelector('.explain-button');
        const detailedDescription = this.node.querySelector('.detailed-description');
        explainButton === null || explainButton === void 0 ? void 0 : explainButton.addEventListener('click', () => {
            if (detailedDescription) {
                detailedDescription.style.display =
                    detailedDescription.style.display === 'none' ? 'block' : 'none';
            }
        });
        // Populate offending content as plain text (not rendered)
        const offendingSnippet = this.node.querySelector('.offending-snippet');
        if (offendingSnippet) {
            offendingSnippet.textContent = `${this.issue.issueContentRaw || ''}`;
        }
        // Show suggest button initially if AI is enabled
        const mainPanelElement = document.getElementById('a11y-sidebar');
        if (mainPanelElement) {
            const aiToggleButton = mainPanelElement.querySelector('.ai-control-button');
            if (aiToggleButton && ((_a = aiToggleButton.textContent) === null || _a === void 0 ? void 0 : _a.includes('Enabled'))) {
                this.aiEnabled = true;
            }
            else {
                this.aiEnabled = false;
            }
        }
        // Dynamically add the TextFieldFixWidget if needed
        const fixWidgetContainer = this.node.querySelector('.fix-widget-container');
        if (!fixWidgetContainer) {
            return;
        }
        if (this.issue.violationId === 'image-missing-alt') {
            const textFieldFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_1__.ImageAltFixWidget(this.issue, this.cell, this.aiEnabled, this.mainPanel.getVisionModelSettings());
            fixWidgetContainer.appendChild(textFieldFixWidget.node);
        }
        else if (this.issue.violationId === 'table-missing-caption') {
            const tableCaptionFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_1__.TableCaptionFixWidget(this.issue, this.cell, this.aiEnabled, this.mainPanel.getLanguageModelSettings());
            fixWidgetContainer.appendChild(tableCaptionFixWidget.node);
        }
        else if (this.issue.violationId === 'table-missing-header') {
            const tableHeaderFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_2__.TableHeaderFixWidget(this.issue, this.cell, this.aiEnabled);
            fixWidgetContainer.appendChild(tableHeaderFixWidget.node);
        }
        else if (this.issue.violationId === 'heading-missing-h1') {
            const headingOneFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_1__.HeadingOneFixWidget(this.issue, this.cell, this.aiEnabled);
            fixWidgetContainer.appendChild(headingOneFixWidget.node);
        }
        else if (this.issue.violationId === 'heading-wrong-order') {
            const headingOrderFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_2__.HeadingOrderFixWidget(this.issue, this.cell, this.aiEnabled);
            fixWidgetContainer.appendChild(headingOrderFixWidget.node);
        }
        else if (this.issue.violationId === 'table-missing-scope') {
            const tableScopeFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_3__.TableScopeFixWidget(this.issue, this.cell, this.aiEnabled);
            fixWidgetContainer.appendChild(tableScopeFixWidget.node);
        }
        else if (this.issue.violationId === 'link-discernible-text') {
            const linkTextFixWidget = new _fix__WEBPACK_IMPORTED_MODULE_1__.LinkTextFixWidget(this.issue, this.cell, this.aiEnabled);
            fixWidgetContainer.appendChild(linkTextFixWidget.node);
        }
    }
    navigateToCell() {
        this.cell.node.scrollIntoView({ behavior: 'auto', block: 'nearest' });
        requestAnimationFrame(() => {
            this.cell.node.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
        this.cell.node.style.transition = 'background-color 0.5s ease';
        this.cell.node.style.backgroundColor = '#DB3939';
        setTimeout(() => {
            this.cell.node.style.backgroundColor = '';
        }, 1000);
    }
}


/***/ }),

/***/ "./lib/components/mainpanelWidget.js":
/*!*******************************************!*\
  !*** ./lib/components/mainpanelWidget.js ***!
  \*******************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   MainPanelWidget: () => (/* binding */ MainPanelWidget)
/* harmony export */ });
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _issueWidget__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./issueWidget */ "./lib/components/issueWidget.js");
/* harmony import */ var _utils_metadata__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../utils/metadata */ "./lib/utils/metadata.js");
/* harmony import */ var _utils_detection_base__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../utils/detection/base */ "./lib/utils/detection/base.js");
/* harmony import */ var _utils_detection_category_table__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../utils/detection/category/table */ "./lib/utils/detection/category/table.js");






class MainPanelWidget extends _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.Widget {
    constructor(settingRegistry) {
        super();
        this.aiEnabled = false;
        this.currentNotebook = null;
        // Default settings
        this.languageModelSettings = {
            baseUrl: '',
            apiKey: '',
            model: ''
        };
        this.visionModelSettings = {
            baseUrl: '',
            apiKey: '',
            model: ''
        };
        // Load settings if available
        if (settingRegistry) {
            this.loadSettings(settingRegistry);
        }
        this.addClass('a11y-panel');
        this.id = 'a11y-sidebar';
        const accessibilityIcon = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_1__.LabIcon({
            name: 'a11y:accessibility',
            svgstr: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="#154F92" d="M256 48c114.953 0 208 93.029 208 208 0 114.953-93.029 208-208 208-114.953 0-208-93.029-208-208 0-114.953 93.029-208 208-208m0-40C119.033 8 8 119.033 8 256s111.033 248 248 248 248-111.033 248-248S392.967 8 256 8zm0 56C149.961 64 64 149.961 64 256s85.961 192 192 192 192-85.961 192-192S362.039 64 256 64zm0 44c19.882 0 36 16.118 36 36s-16.118 36-36 36-36-16.118-36-36 16.118-36 36-36zm117.741 98.023c-28.712 6.779-55.511 12.748-82.14 15.807.851 101.023 12.306 123.052 25.037 155.621 3.617 9.26-.957 19.698-10.217 23.315-9.261 3.617-19.699-.957-23.316-10.217-8.705-22.308-17.086-40.636-22.261-78.549h-9.686c-5.167 37.851-13.534 56.208-22.262 78.549-3.615 9.255-14.05 13.836-23.315 10.217-9.26-3.617-13.834-14.056-10.217-23.315 12.713-32.541 24.185-54.541 25.037-155.621-26.629-3.058-53.428-9.027-82.141-15.807-8.6-2.031-13.926-10.648-11.895-19.249s10.647-13.926 19.249-11.895c96.686 22.829 124.283 22.783 220.775 0 8.599-2.03 17.218 3.294 19.249 11.895 2.029 8.601-3.297 17.219-11.897 19.249z"/></svg>'
        });
        this.title.icon = accessibilityIcon;
        this.node.innerHTML = `
      <div class="main-container">
          <div class="notice-container">
              <div class="notice-header">
                  <div class="notice-title">
                      <span class="chevron material-icons">expand_more</span>
                      <strong>Notice: Known cell navigation error </strong>
                  </div>
                  <button class="notice-delete-button">✕</button>
              </div>
              <div class="notice-content hidden">
                  <p>
                      The jupyterlab-a11y-checker has a known cell navigation issue for Jupyterlab version 4.2.5 or later. 
                      To fix this, please navigate to 'Settings' → 'Settings Editor' → Notebook, scroll down to 'Windowing mode', 
                      and choose 'defer' from the dropdown. Please note that this option may reduce the performance of the application. 
                      For more information, please see the <a href="https://jupyter-notebook.readthedocs.io/en/stable/changelog.html" target="_blank" style="text-decoration: underline;">Jupyter Notebook changelog.</a>
                  </p>
              </div>
          </div>
          <h1 class="main-title">Accessibility Checker</h1>
          <div class="controls-container">
              <button class="control-button ai-control-button">
                <span class="material-icons">auto_awesome</span>
                Use AI : Disabled
              </button>
              <button class="control-button analyze-control-button">
                <span class="material-icons">science</span>  
                Analyze Notebook
              </button>
          </div>
          <div class="issues-container"></div>
      </div>
        `;
        // Notice
        const noticeContainer = this.node.querySelector('.notice-container');
        const noticeContent = this.node.querySelector('.notice-content');
        const noticeToggleButton = this.node.querySelector('.notice-title');
        const noticeDeleteButton = this.node.querySelector('.notice-delete-button');
        const expandIcon = this.node.querySelector('.chevron');
        noticeToggleButton === null || noticeToggleButton === void 0 ? void 0 : noticeToggleButton.addEventListener('click', () => {
            noticeContent === null || noticeContent === void 0 ? void 0 : noticeContent.classList.toggle('hidden');
            expandIcon === null || expandIcon === void 0 ? void 0 : expandIcon.classList.toggle('expanded');
        });
        noticeDeleteButton === null || noticeDeleteButton === void 0 ? void 0 : noticeDeleteButton.addEventListener('click', () => {
            noticeContainer === null || noticeContainer === void 0 ? void 0 : noticeContainer.classList.add('hidden');
        });
        // Controls
        const aiControlButton = this.node.querySelector('.ai-control-button');
        const analyzeControlButton = this.node.querySelector('.analyze-control-button');
        const progressIcon = `
    <svg class="icon loading" viewBox="0 0 24 24">
        <path d="M12 4V2C6.48 2 2 6.48 2 12h2c0-4.41 3.59-8 8-8z"/>
    </svg>
    `;
        aiControlButton === null || aiControlButton === void 0 ? void 0 : aiControlButton.addEventListener('click', async () => {
            const aiIcon = '<span class="material-icons">auto_awesome</span>';
            this.aiEnabled = !this.aiEnabled;
            aiControlButton.innerHTML = `${aiIcon} Use AI : ${this.aiEnabled ? 'Enabled' : 'Disabled'}`;
            // Update every ai suggestion button visibility
            const suggestButtons = this.node.querySelectorAll('.suggest-button');
            suggestButtons.forEach(button => {
                button.style.display = this.aiEnabled
                    ? 'flex'
                    : 'none';
            });
        });
        analyzeControlButton === null || analyzeControlButton === void 0 ? void 0 : analyzeControlButton.addEventListener('click', async () => {
            if (!this.currentNotebook) {
                console.log('No current notebook found');
                return;
            }
            const analyzeControlButtonText = analyzeControlButton.innerHTML;
            const issuesContainer = this.node.querySelector('.issues-container');
            issuesContainer.innerHTML = '';
            analyzeControlButton.innerHTML = `${progressIcon} Please wait...`;
            analyzeControlButton.disabled = true;
            try {
                // Identify issues
                const notebookIssues = await (0,_utils_detection_base__WEBPACK_IMPORTED_MODULE_4__.analyzeCellsAccessibility)(this.currentNotebook);
                // Log a human-readable summary for troubleshooting
                try {
                    const total = notebookIssues.length;
                    const byViolation = notebookIssues.reduce((acc, issue) => {
                        acc[issue.violationId] = (acc[issue.violationId] || 0) + 1;
                        return acc;
                    }, {});
                    const cellsAffected = Array.from(new Set(notebookIssues.map(i => i.cellIndex))).length;
                    const lines = [];
                    lines.push('A11Y Analysis Summary');
                    lines.push(`- Total issues: ${total}`);
                    lines.push(`- Cells affected: ${cellsAffected}`);
                    const allViolations = Object.entries(byViolation)
                        .sort((a, b) => b[1] - a[1])
                        .map(([v, c]) => `  - ${v}: ${c}`);
                    if (allViolations.length) {
                        lines.push('- Violations:');
                        lines.push(...allViolations);
                    }
                    console.log(lines.join('\n'));
                }
                catch (_a) {
                    console.log('Summary Unavailable');
                }
                if (notebookIssues.length === 0) {
                    issuesContainer.innerHTML =
                        '<div class="no-issues">No issues found</div>';
                    return;
                }
                // Group issues by category
                const issuesByCategory = new Map();
                notebookIssues.forEach(notebookIssue => {
                    const categoryName = _utils_metadata__WEBPACK_IMPORTED_MODULE_3__.issueToCategory.get(notebookIssue.violationId) || 'Other';
                    if (!issuesByCategory.has(categoryName)) {
                        issuesByCategory.set(categoryName, []);
                    }
                    issuesByCategory.get(categoryName).push(notebookIssue);
                });
                // Create widgets for each category
                for (const categoryName of _utils_metadata__WEBPACK_IMPORTED_MODULE_3__.issueCategoryNames) {
                    const categoryIssues = issuesByCategory.get(categoryName) || [];
                    if (categoryIssues.length === 0) {
                        continue;
                    }
                    const categoryWidget = document.createElement('div');
                    categoryWidget.classList.add('category');
                    categoryWidget.innerHTML = `
            <h2 class="category-title">${categoryName}</h2>
            <hr>
            <div class="issues-list"></div>
          `;
                    const issuesContainer = this.node.querySelector('.issues-container');
                    issuesContainer.appendChild(categoryWidget);
                    const issuesList = categoryWidget.querySelector('.issues-list');
                    categoryIssues.forEach(issue => {
                        const issueWidget = new _issueWidget__WEBPACK_IMPORTED_MODULE_2__.CellIssueWidget(issue, this.currentNotebook.content.widgets[issue.cellIndex], this.aiEnabled, this);
                        issuesList.appendChild(issueWidget.node);
                    });
                }
            }
            catch (error) {
                issuesContainer.innerHTML = '';
                console.error('Error analyzing notebook:', error);
            }
            finally {
                analyzeControlButton.innerHTML = analyzeControlButtonText;
                analyzeControlButton.disabled = false;
            }
        });
        // Add event listener for notebookReanalyzed event
        // Listen on both the panel node and document to ensure we catch bubbled events
        const handler = async (event) => {
            var _a, _b, _c;
            const customEvent = event;
            const newIssues = customEvent.detail.issues;
            const isHeadingUpdate = customEvent.detail.isHeadingUpdate;
            const isTableUpdate = customEvent.detail.isTableUpdate;
            const isCellUpdate = customEvent.detail.isCellUpdate;
            if (isHeadingUpdate) {
                // Find the Headings category section
                const headingsCategory = (_a = Array.from(this.node.querySelectorAll('.category-title'))
                    .find(title => title.textContent === 'Headings')) === null || _a === void 0 ? void 0 : _a.closest('.category');
                if (headingsCategory) {
                    // Clear only the issues list in the Headings section
                    const issuesList = headingsCategory.querySelector('.issues-list');
                    if (issuesList) {
                        issuesList.innerHTML = '';
                        // Add new heading issues to this section
                        newIssues.forEach((issue) => {
                            const issueWidget = new _issueWidget__WEBPACK_IMPORTED_MODULE_2__.CellIssueWidget(issue, this.currentNotebook.content.widgets[issue.cellIndex], this.aiEnabled, this);
                            issuesList.appendChild(issueWidget.node);
                        });
                    }
                }
            }
            else if (isTableUpdate) {
                // Find the Tables category section
                const tablesCategory = (_b = Array.from(this.node.querySelectorAll('.category-title'))
                    .find(title => title.textContent === 'Tables')) === null || _b === void 0 ? void 0 : _b.closest('.category');
                if (tablesCategory) {
                    // Clear only the issues list in the Tables section
                    const issuesList = tablesCategory.querySelector('.issues-list');
                    if (issuesList) {
                        issuesList.innerHTML = '';
                        // Reanalyze table issues
                        const tableIssues = await (0,_utils_detection_category_table__WEBPACK_IMPORTED_MODULE_5__.analyzeTableIssues)(this.currentNotebook);
                        // Add new table issues to this section
                        tableIssues.forEach((issue) => {
                            const issueWidget = new _issueWidget__WEBPACK_IMPORTED_MODULE_2__.CellIssueWidget(issue, this.currentNotebook.content.widgets[issue.cellIndex], this.aiEnabled, this);
                            issuesList.appendChild(issueWidget.node);
                        });
                    }
                }
            }
            else if (isCellUpdate) {
                // Single-cell update: replace only issues from impacted cell(s) per category
                const incomingIssues = newIssues;
                const issuesByCategory = new Map();
                incomingIssues.forEach(issue => {
                    const categoryName = _utils_metadata__WEBPACK_IMPORTED_MODULE_3__.issueToCategory.get(issue.violationId) || 'Other';
                    if (!issuesByCategory.has(categoryName)) {
                        issuesByCategory.set(categoryName, []);
                    }
                    issuesByCategory.get(categoryName).push(issue);
                });
                for (const [categoryName, categoryIssues] of issuesByCategory) {
                    // Find or create the category section
                    let categoryEl = (_c = Array.from(this.node.querySelectorAll('.category-title'))
                        .find(title => title.textContent === categoryName)) === null || _c === void 0 ? void 0 : _c.closest('.category');
                    if (!categoryEl) {
                        categoryEl = document.createElement('div');
                        categoryEl.classList.add('category');
                        categoryEl.innerHTML = `
              <h2 class="category-title">${categoryName}</h2>
              <hr>
              <div class="issues-list"></div>
            `;
                        const container = this.node.querySelector('.issues-container');
                        container.appendChild(categoryEl);
                    }
                    const issuesList = categoryEl.querySelector('.issues-list');
                    // Remove existing widgets for impacted cell indices only
                    const impacted = new Set(categoryIssues.map(i => i.cellIndex));
                    Array.from(issuesList.children).forEach(child => {
                        const el = child;
                        const idxAttr = el.getAttribute('data-cell-index');
                        if (idxAttr && impacted.has(parseInt(idxAttr))) {
                            el.remove();
                        }
                    });
                    // Append new issues for this category
                    categoryIssues.forEach(issue => {
                        const issueWidget = new _issueWidget__WEBPACK_IMPORTED_MODULE_2__.CellIssueWidget(issue, this.currentNotebook.content.widgets[issue.cellIndex], this.aiEnabled, this);
                        issuesList.appendChild(issueWidget.node);
                    });
                }
            }
        };
        this.node.addEventListener('notebookReanalyzed', handler);
        //document.addEventListener('notebookReanalyzed', handler as EventListener);
    }
    async loadSettings(settingRegistry) {
        try {
            const settings = await settingRegistry.load('jupyterlab-a11y-checker:plugin');
            if (settings.get('languageModel').composite) {
                const langModel = settings.get('languageModel').composite;
                this.languageModelSettings = {
                    baseUrl: langModel.baseUrl || this.languageModelSettings.baseUrl,
                    apiKey: langModel.apiKey || this.languageModelSettings.apiKey,
                    model: langModel.model || this.languageModelSettings.model
                };
            }
            if (settings.get('visionModel').composite) {
                const visionModel = settings.get('visionModel').composite;
                this.visionModelSettings = {
                    baseUrl: visionModel.baseUrl || this.visionModelSettings.baseUrl,
                    apiKey: visionModel.apiKey || this.visionModelSettings.apiKey,
                    model: visionModel.model || this.visionModelSettings.model
                };
            }
        }
        catch (error) {
            console.warn('Failed to load settings:', error);
        }
    }
    getLanguageModelSettings() {
        return this.languageModelSettings;
    }
    getVisionModelSettings() {
        return this.visionModelSettings;
    }
    setNotebook(notebook) {
        this.currentNotebook = notebook;
        const issuesContainer = this.node.querySelector('.issues-container');
        issuesContainer.innerHTML = '';
    }
}


/***/ }),

/***/ "./lib/index.js":
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/notebook */ "webpack/sharing/consume/default/@jupyterlab/notebook");
/* harmony import */ var _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_application__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/application */ "webpack/sharing/consume/default/@jupyterlab/application");
/* harmony import */ var _jupyterlab_application__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_application__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/settingregistry */ "webpack/sharing/consume/default/@jupyterlab/settingregistry");
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _components_mainpanelWidget__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./components/mainpanelWidget */ "./lib/components/mainpanelWidget.js");




const extension = {
    id: 'jupyterlab-a11y-checker:plugin',
    autoStart: true,
    requires: [_jupyterlab_application__WEBPACK_IMPORTED_MODULE_1__.ILabShell, _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__.ISettingRegistry],
    activate: (app, labShell, settingRegistry) => {
        const panel = new _components_mainpanelWidget__WEBPACK_IMPORTED_MODULE_3__.MainPanelWidget(settingRegistry);
        labShell.add(panel, 'right');
        // Update current notebook when active widget changes
        labShell.currentChanged.connect(() => {
            const current = labShell.currentWidget;
            if (current instanceof _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0__.NotebookPanel) {
                panel.setNotebook(current);
            }
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (extension);


/***/ }),

/***/ "./lib/utils/ai-utils.js":
/*!*******************************!*\
  !*** ./lib/utils/ai-utils.js ***!
  \*******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   getImageAltSuggestion: () => (/* binding */ getImageAltSuggestion),
/* harmony export */   getTableCaptionSuggestion: () => (/* binding */ getTableCaptionSuggestion)
/* harmony export */ });
/* harmony import */ var _http__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./http */ "./lib/utils/http.js");

async function fetchImageAsBase64(imageUrl) {
    /**
     * Function that fetches image from url, converts to JPEG, and returns in base64 format.
     * Similar to the Python convert_to_jpeg_base64 function in your notebook.
     */
    const response = await _http__WEBPACK_IMPORTED_MODULE_0__.http.get(imageUrl, { responseType: 'blob' });
    const imageBlob = response.data;
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            // Create canvas and draw image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                reject(new Error('Could not get canvas context'));
                return;
            }
            // Set canvas size to image size
            canvas.width = img.width;
            canvas.height = img.height;
            // If image has transparency, fill with white background first
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            // Draw the image on canvas
            ctx.drawImage(img, 0, 0);
            // Convert to JPEG base64 (quality 95% like in the Python example)
            const jpegDataUrl = canvas.toDataURL('image/jpeg', 0.95);
            // Extract just the base64 part (remove "data:image/jpeg;base64,")
            const base64String = jpegDataUrl.split(',')[1];
            resolve(base64String);
        };
        img.onerror = () => {
            reject(new Error('Failed to load image'));
        };
        // Create object URL from blob and load it
        const objectUrl = URL.createObjectURL(imageBlob);
        img.src = objectUrl;
    });
}
async function getImageAltSuggestion(issue, imageData, visionSettings) {
    let prompt = 'Read the provided image and respond with a short description of the image, without any explanation. Avoid using the word "image" in the description.';
    prompt += `Content: \n${issue.issueContentRaw}\n\n`;
    // New River implementation - using OpenAI Chat Completions API format
    try {
        const imageUrl = imageData.startsWith('data:image')
            ? imageData
            : `data:image/jpeg;base64,${await fetchImageAsBase64(imageData)}`;
        const body = JSON.stringify({
            model: visionSettings.model,
            messages: [
                {
                    role: 'system',
                    content: 'You are a helpful assistant that generates alt text for images.'
                },
                {
                    role: 'user',
                    content: [
                        {
                            type: 'text',
                            text: prompt
                        },
                        {
                            type: 'image_url',
                            image_url: {
                                url: imageUrl
                            }
                        }
                    ]
                }
            ],
            max_tokens: 150
        });
        const response = await _http__WEBPACK_IMPORTED_MODULE_0__.http.post(visionSettings.baseUrl, body, {
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${visionSettings.apiKey}`
            }
        });
        // Parse response using OpenAI Chat Completions format
        if (response.data.choices &&
            response.data.choices[0] &&
            response.data.choices[0].message) {
            const responseText = response.data.choices[0].message.content;
            return responseText ? responseText.trim() : 'No content in response';
        }
        else {
            console.error('Unexpected response structure:', response.data);
            return 'Error parsing response';
        }
    }
    catch (error) {
        console.error('Error getting suggestions:', error);
        return 'Error';
    }
}
async function getTableCaptionSuggestion(issue, languageSettings) {
    const prompt = `Given this HTML table, please provide a caption for the table to be served as a title or heading for the table. Avoid using the word "table" in the caption. Here's the table:
    ${issue.issueContentRaw}`;
    // New River implementation - using OpenAI Chat Completions API format
    try {
        const body = JSON.stringify({
            model: languageSettings.model,
            messages: [
                {
                    role: 'system',
                    content: 'You are a helpful assistant that generates captions for HTML tables.'
                },
                {
                    role: 'user',
                    content: prompt
                }
            ],
            max_tokens: 150
        });
        const response = await _http__WEBPACK_IMPORTED_MODULE_0__.http.post(languageSettings.baseUrl, body, {
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${languageSettings.apiKey}`
            }
        });
        // Parse response using OpenAI Chat Completions format
        if (response.data.choices &&
            response.data.choices[0] &&
            response.data.choices[0].message) {
            const responseText = response.data.choices[0].message.content;
            return responseText ? responseText.trim() : 'No content in response';
        }
        else {
            console.error('Unexpected response structure:', response.data);
            return 'Error parsing response';
        }
    }
    catch (error) {
        console.error('Error getting suggestions:', error);
        return 'Error';
    }
}


/***/ }),

/***/ "./lib/utils/detection/base.js":
/*!*************************************!*\
  !*** ./lib/utils/detection/base.js ***!
  \*************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   analyzeCellIssues: () => (/* binding */ analyzeCellIssues),
/* harmony export */   analyzeCellsAccessibility: () => (/* binding */ analyzeCellsAccessibility)
/* harmony export */ });
/* harmony import */ var axe_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! axe-core */ "webpack/sharing/consume/default/axe-core/axe-core");
/* harmony import */ var axe_core__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(axe_core__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var marked__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! marked */ "webpack/sharing/consume/default/marked/marked");
/* harmony import */ var marked__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(marked__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _category_heading__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./category/heading */ "./lib/utils/detection/category/heading.js");
/* harmony import */ var _category__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./category */ "./lib/utils/detection/category/image.js");
/* harmony import */ var _category__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./category */ "./lib/utils/detection/category/table.js");
/* harmony import */ var _category__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./category */ "./lib/utils/detection/category/color.js");
/* harmony import */ var _category__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./category */ "./lib/utils/detection/category/link.js");







async function analyzeCellsAccessibility(panel) {
    const notebookIssues = [];
    const cells = panel.content.widgets;
    // Add heading one check
    notebookIssues.push(...(await (0,_category_heading__WEBPACK_IMPORTED_MODULE_2__.detectHeadingOneIssue)('', 0, 'markdown', cells)));
    const tempDiv = document.createElement('div');
    document.body.appendChild(tempDiv);
    const axeConfig = {
        runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
        rules: {
            'image-alt': { enabled: false },
            'empty-heading': { enabled: false },
            'heading-order': { enabled: false },
            'page-has-heading-one': { enabled: false },
            'link-name': { enabled: false }
        }
    };
    try {
        // First, analyze heading hierarchy across the notebook
        const headingIssues = await (0,_category_heading__WEBPACK_IMPORTED_MODULE_2__.analyzeHeadingHierarchy)(panel);
        notebookIssues.push(...headingIssues);
        // Then analyze individual cells for other issues
        for (let i = 0; i < cells.length; i++) {
            const cell = cells[i];
            if (!cell || !cell.model) {
                console.warn(`Skipping cell ${i}: Invalid cell or model`);
                continue;
            }
            const cellType = cell.model.type;
            if (cellType === 'markdown') {
                const rawMarkdown = cell.model.sharedModel.getSource();
                if (rawMarkdown.trim()) {
                    tempDiv.innerHTML = await marked__WEBPACK_IMPORTED_MODULE_1__.marked.parse(rawMarkdown);
                    const results = await axe_core__WEBPACK_IMPORTED_MODULE_0___default().run(tempDiv, axeConfig);
                    const violations = results.violations;
                    // Can have multiple violations in a single cell
                    if (violations.length > 0) {
                        violations.forEach(violation => {
                            violation.nodes.forEach(node => {
                                notebookIssues.push({
                                    cellIndex: i,
                                    cellType: cellType,
                                    violationId: violation.id,
                                    issueContentRaw: node.html
                                });
                            });
                        });
                    }
                    // Add custom image issue detection
                    const folderPath = panel.context.path.substring(0, panel.context.path.lastIndexOf('/'));
                    // Image Issues
                    notebookIssues.push(...(await (0,_category__WEBPACK_IMPORTED_MODULE_3__.detectImageIssuesInCell)(rawMarkdown, i, cellType, folderPath)));
                    // Table Issues
                    notebookIssues.push(...(0,_category__WEBPACK_IMPORTED_MODULE_4__.detectTableIssuesInCell)(rawMarkdown, i, cellType));
                    // Color Issues
                    notebookIssues.push(...(await (0,_category__WEBPACK_IMPORTED_MODULE_5__.detectColorIssuesInCell)(rawMarkdown, i, cellType, folderPath, panel // Pass panel for attachment handling
                    )));
                    // Link Issues
                    notebookIssues.push(...(0,_category__WEBPACK_IMPORTED_MODULE_6__.detectLinkIssuesInCell)(rawMarkdown, i, cellType));
                }
            }
            else if (cellType === 'code') {
                const codeInput = cell.node.querySelector('.jp-InputArea-editor');
                const codeOutput = cell.node.querySelector('.jp-OutputArea');
                if (codeInput || codeOutput) {
                    // We would have to feed this into a language model to get the suggested fix.
                }
            }
        }
    }
    finally {
        tempDiv.remove();
    }
    return notebookIssues;
}
// Analyze a single cell (content-based categories only). Headings are excluded
// because heading structure depends on the entire notebook.
async function analyzeCellIssues(panel, cellIndex) {
    const issues = [];
    const cells = panel.content.widgets;
    const cell = cells[cellIndex];
    if (!cell || !cell.model) {
        return issues;
    }
    const cellType = cell.model.type;
    if (cellType !== 'markdown') {
        return issues;
    }
    const rawMarkdown = cell.model.sharedModel.getSource();
    if (!rawMarkdown.trim()) {
        return issues;
    }
    const folderPath = panel.context.path.substring(0, panel.context.path.lastIndexOf('/'));
    // Images
    issues.push(...(await (0,_category__WEBPACK_IMPORTED_MODULE_3__.detectImageIssuesInCell)(rawMarkdown, cellIndex, cellType, folderPath)));
    // Tables
    issues.push(...(0,_category__WEBPACK_IMPORTED_MODULE_4__.detectTableIssuesInCell)(rawMarkdown, cellIndex, cellType));
    // Color
    issues.push(...(await (0,_category__WEBPACK_IMPORTED_MODULE_5__.detectColorIssuesInCell)(rawMarkdown, cellIndex, cellType, folderPath, panel)));
    // Links
    issues.push(...(0,_category__WEBPACK_IMPORTED_MODULE_6__.detectLinkIssuesInCell)(rawMarkdown, cellIndex, cellType));
    return issues;
}


/***/ }),

/***/ "./lib/utils/detection/category/color.js":
/*!***********************************************!*\
  !*** ./lib/utils/detection/category/color.js ***!
  \***********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   detectColorIssuesInCell: () => (/* binding */ detectColorIssuesInCell)
/* harmony export */ });
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var tesseract_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! tesseract.js */ "webpack/sharing/consume/default/tesseract.js/tesseract.js");
/* harmony import */ var tesseract_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(tesseract_js__WEBPACK_IMPORTED_MODULE_1__);


function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return { r, g, b };
}
function calculateLuminance(rgb) {
    const a = [rgb.r, rgb.g, rgb.b].map(v => {
        v /= 255;
        return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}
function calculateContrast(foregroundHex, backgroundHex) {
    const rgb1 = hexToRgb(foregroundHex);
    const rgb2 = hexToRgb(backgroundHex);
    const L1 = calculateLuminance(rgb1);
    const L2 = calculateLuminance(rgb2);
    const lighter = Math.max(L1, L2);
    const darker = Math.min(L1, L2);
    return (lighter + 0.05) / (darker + 0.05);
}
/**
 * Extract image data from a JupyterLab attachment
 * @param attachmentId The ID of the attachment (e.g., 'c6533816-e12f-47fb-8896-af4065f8a12f.png')
 * @param panel The notebook panel containing the attachment
 * @param cellIndex The index of the cell containing the attachment
 * @returns Data URL for the image or null if not found
 */
async function getAttachmentDataUrl(attachmentId, panel, cellIndex) {
    try {
        // Extract filename from attachment ID
        if (!panel.model) {
            console.warn('No notebook model available');
            return null;
        }
        const cell = panel.content.widgets[cellIndex];
        if (!cell || !cell.model) {
            console.warn(`Cell at index ${cellIndex} is not available`);
            return null;
        }
        try {
            // Access the cell data directly
            const cellData = cell.model.toJSON();
            if (cellData &&
                cellData.attachments &&
                cellData.attachments[attachmentId]) {
                const data = cellData.attachments[attachmentId];
                // Get the base64 data
                if (data && typeof data === 'object') {
                    for (const mimetype in data) {
                        if (mimetype.startsWith('image/')) {
                            const base64 = data[mimetype];
                            if (typeof base64 === 'string') {
                                return `data:${mimetype};base64,${base64}`;
                            }
                        }
                    }
                }
            }
        }
        catch (e) {
            console.error('Error accessing cell widget data:', e);
        }
        return null;
    }
    catch (error) {
        console.error('Error extracting attachment:', error);
        return null;
    }
}
async function getColorContrastInImage(imagePath, currentDirectoryPath, panel, cellIndex) {
    // Determine the source for the image
    let imageSource;
    // Check if this is a JupyterLab attachment
    if (imagePath.startsWith('attachment:')) {
        if (!panel || cellIndex === undefined) {
            throw new Error('NotebookPanel and cellIndex required for attachment images');
        }
        const attachmentId = imagePath.substring('attachment:'.length);
        const dataUrl = await getAttachmentDataUrl(attachmentId, panel, cellIndex);
        if (!dataUrl) {
            throw new Error(`Could not load attachment: ${attachmentId}`);
        }
        imageSource = dataUrl;
    }
    else {
        // Regular image path (local or remote)
        imageSource = imagePath.startsWith('http')
            ? imagePath
            : `${_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__.PageConfig.getBaseUrl()}files/${currentDirectoryPath}/${imagePath}`;
    }
    // Create canvas and load image
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.src = imageSource;
    return new Promise((resolve, reject) => {
        img.onload = async () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                reject(new Error('Could not get canvas context'));
                return;
            }
            // Draw image
            ctx.drawImage(img, 0, 0);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            try {
                // Create Tesseract worker
                const worker = await tesseract_js__WEBPACK_IMPORTED_MODULE_1___default().createWorker();
                // Set PSM mode to SPARSE_TEXT (11)
                await worker.setParameters({
                    tessedit_pageseg_mode: tesseract_js__WEBPACK_IMPORTED_MODULE_1__.PSM.SPARSE_TEXT
                });
                // Recognize text blocks with PSM 11
                const result = await worker.recognize(canvas, {}, { blocks: true });
                if (result.data.confidence < 40) {
                    // We can't analyze the image, so we return the default values
                    resolve({
                        contrast: 21,
                        isAccessible: true,
                        hasLargeText: false
                    });
                    return;
                }
                let minContrast = 21; // Default to maximum contrast
                let hasLargeText = false;
                // Process each text block
                if (result.data.blocks && result.data.blocks.length > 0) {
                    result.data.blocks.forEach(block => {
                        const { x0, y0, x1, y1 } = block.bbox;
                        const textHeight = y1 - y0;
                        // Check if text is large (>= 24px height)
                        if (textHeight >= 24) {
                            hasLargeText = true;
                        }
                        // Get colors from the block area
                        const colorCount = {};
                        const data = imageData.data;
                        const width = imageData.width;
                        // Sample colors from the block area
                        for (let y = y0; y <= y1; y++) {
                            for (let x = x0; x <= x1; x++) {
                                const index = (y * width + x) * 4;
                                const r = data[index];
                                const g = data[index + 1];
                                const b = data[index + 2];
                                // Skip transparent pixels
                                if (data[index + 3] < 128) {
                                    continue;
                                }
                                // Quantize colors to reduce unique values
                                const scale = 30;
                                const colorKey = '#' +
                                    ((1 << 24) +
                                        ((Math.floor(r / scale) * scale) << 16) +
                                        ((Math.floor(g / scale) * scale) << 8) +
                                        Math.floor(b / scale) * scale)
                                        .toString(16)
                                        .slice(1)
                                        .toUpperCase();
                                colorCount[colorKey] = (colorCount[colorKey] || 0) + 1;
                            }
                        }
                        // Get the two most common colors
                        const sortedColors = Object.entries(colorCount).sort((a, b) => b[1] - a[1]);
                        if (sortedColors.length >= 2) {
                            const bgColor = sortedColors[0][0];
                            const fgColor = sortedColors[1][0];
                            // Calculate contrast ratio
                            const contrast = calculateContrast(fgColor, bgColor);
                            // Update minimum contrast
                            if (contrast < minContrast) {
                                minContrast = contrast;
                            }
                        }
                    });
                }
                // Determine if the contrast meets WCAG standards (4.5:1 for normal text)
                const isAccessible = hasLargeText
                    ? minContrast >= 3
                    : minContrast >= 4.5;
                // Terminate the worker
                await worker.terminate();
                resolve({
                    contrast: minContrast,
                    isAccessible,
                    hasLargeText
                });
            }
            catch (error) {
                console.error('Error analyzing image with Tesseract:', error);
                // Fallback to analyzing the entire image
                const colorCount = {};
                const data = imageData.data;
                const width = imageData.width;
                const height = imageData.height;
                // Sample colors from the image (every 10th pixel to improve performance)
                for (let y = 0; y < height; y += 10) {
                    for (let x = 0; x < width; x += 10) {
                        const index = (y * width + x) * 4;
                        const r = data[index];
                        const g = data[index + 1];
                        const b = data[index + 2];
                        // Skip transparent pixels
                        if (data[index + 3] < 128) {
                            continue;
                        }
                        // Quantize colors to reduce unique values
                        const scale = 30;
                        const colorKey = '#' +
                            ((1 << 24) +
                                ((Math.floor(r / scale) * scale) << 16) +
                                ((Math.floor(g / scale) * scale) << 8) +
                                Math.floor(b / scale) * scale)
                                .toString(16)
                                .slice(1)
                                .toUpperCase();
                        colorCount[colorKey] = (colorCount[colorKey] || 0) + 1;
                    }
                }
                // Get the two most common colors
                const sortedColors = Object.entries(colorCount).sort((a, b) => b[1] - a[1]);
                let contrast = 21; // Default to maximum contrast
                if (sortedColors.length >= 2) {
                    const bgColor = sortedColors[0][0];
                    const fgColor = sortedColors[1][0];
                    // Calculate contrast ratio
                    contrast = calculateContrast(fgColor, bgColor);
                }
                // Determine if the contrast meets WCAG standards (4.5:1 for normal text)
                const isAccessible = contrast >= 4.5;
                resolve({
                    contrast,
                    isAccessible,
                    hasLargeText: false // Default to false in fallback case
                });
            }
        };
        img.onerror = e => {
            console.error('Image load error:', e);
            reject(new Error('Failed to load image'));
        };
    });
}
async function detectColorIssuesInCell(rawMarkdown, cellIndex, cellType, notebookPath, panel) {
    var _a, _b, _c, _d, _e, _f;
    const notebookIssues = [];
    // Check for all images in markdown syntax (this will also catch attachment syntax)
    const mdSyntaxImageRegex = /!\[[^\]]*\]\([^)]+\)/g;
    // Check for all images in HTML syntax
    const htmlSyntaxImageRegex = /<img[^>]*>(?:<\/img>)?/g;
    let match;
    while ((match = mdSyntaxImageRegex.exec(rawMarkdown)) !== null ||
        (match = htmlSyntaxImageRegex.exec(rawMarkdown)) !== null) {
        const imageUrl = ((_a = match[0].match(/\(([^)]+)\)/)) === null || _a === void 0 ? void 0 : _a[1]) ||
            ((_b = match[0].match(/src="([^"]+)"/)) === null || _b === void 0 ? void 0 : _b[1]);
        if (imageUrl) {
            const suggestedFix = '';
            try {
                // getColorContrastInImage will handle both regular images and attachments
                const { contrast, isAccessible, hasLargeText } = await getColorContrastInImage(imageUrl, notebookPath, panel, cellIndex);
                if (!isAccessible) {
                    if (hasLargeText) {
                        notebookIssues.push({
                            cellIndex,
                            cellType: cellType,
                            violationId: 'color-insufficient-cc-large',
                            customDescription: `Ensure that a text in an image has sufficient color contrast. The text contrast ratio is ${contrast.toFixed(2)}:1, which is below the required ${hasLargeText ? '3:1' : '4.5:1'} ratio for ${hasLargeText ? 'large' : 'normal'} text.`,
                            issueContentRaw: match[0],
                            metadata: {
                                offsetStart: (_c = match.index) !== null && _c !== void 0 ? _c : 0,
                                offsetEnd: ((_d = match.index) !== null && _d !== void 0 ? _d : 0) + match[0].length
                            },
                            suggestedFix: suggestedFix
                        });
                    }
                    else {
                        notebookIssues.push({
                            cellIndex,
                            cellType: cellType,
                            violationId: 'color-insufficient-cc-normal',
                            customDescription: `Ensure that a large text in an image has sufficient color contrast. The text contrast ratio is ${contrast.toFixed(2)}:1, which is below the required ${hasLargeText ? '3:1' : '4.5:1'} ratio for ${hasLargeText ? 'large' : 'normal'} text.`,
                            issueContentRaw: match[0],
                            metadata: {
                                offsetStart: (_e = match.index) !== null && _e !== void 0 ? _e : 0,
                                offsetEnd: ((_f = match.index) !== null && _f !== void 0 ? _f : 0) + match[0].length
                            },
                            suggestedFix: suggestedFix
                        });
                    }
                }
            }
            catch (error) {
                console.error(`Failed to process image ${imageUrl}:`, error);
            }
        }
    }
    return notebookIssues;
}


/***/ }),

/***/ "./lib/utils/detection/category/heading.js":
/*!*************************************************!*\
  !*** ./lib/utils/detection/category/heading.js ***!
  \*************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   analyzeHeadingHierarchy: () => (/* binding */ analyzeHeadingHierarchy),
/* harmony export */   detectHeadingOneIssue: () => (/* binding */ detectHeadingOneIssue)
/* harmony export */ });
/* harmony import */ var marked__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! marked */ "webpack/sharing/consume/default/marked/marked");
/* harmony import */ var marked__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(marked__WEBPACK_IMPORTED_MODULE_0__);

async function detectHeadingOneIssue(rawMarkdown, cellIndex, cellType, cells) {
    const notebookIssues = [];
    const tempDiv = document.createElement('div');
    // Find the first heading in the notebook
    let firstHeadingFound = false;
    // Check if first cell is a code cell
    if (cells.length > 0 && cells[0].model.type === 'code') {
        notebookIssues.push({
            cellIndex: 0,
            cellType: 'code',
            violationId: 'heading-missing-h1',
            issueContentRaw: ''
        });
    }
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        if (cell.model.type !== 'markdown') {
            continue;
        }
        const content = cell.model.sharedModel.getSource();
        if (!content.trim()) {
            continue;
        }
        // Use marked tokens to find the first heading and offsets in source
        const tokens = marked__WEBPACK_IMPORTED_MODULE_0__.marked.lexer(content);
        let searchStart = 0;
        let foundFirst = false;
        for (const token of tokens) {
            let level = null;
            let rawHeading = '';
            if (token.type === 'heading') {
                level = token.depth;
                rawHeading = token.raw || '';
            }
            else if (token.type === 'html') {
                const rawHtml = token.raw || '';
                const m = rawHtml.match(/<h([1-6])[^>]*>[\s\S]*?<\/h\1>/i);
                if (m) {
                    level = parseInt(m[1], 10);
                    rawHeading = m[0];
                }
            }
            if (level !== null) {
                const start = content.indexOf(rawHeading, searchStart);
                if (start === -1) {
                    continue;
                }
                const end = start + rawHeading.length;
                searchStart = end;
                firstHeadingFound = true;
                if (level !== 1) {
                    notebookIssues.push({
                        cellIndex: i,
                        cellType: 'markdown',
                        violationId: 'heading-missing-h1',
                        issueContentRaw: rawHeading
                    });
                }
                foundFirst = true;
                break;
            }
        }
        if (foundFirst) {
            break;
        }
    }
    // If no headings found at all, suggest adding h1 at the top
    if (!firstHeadingFound) {
        notebookIssues.push({
            cellIndex: 0,
            cellType: 'markdown',
            violationId: 'heading-missing-h1',
            issueContentRaw: ''
        });
    }
    tempDiv.remove();
    return notebookIssues;
}
async function analyzeHeadingHierarchy(panel) {
    const notebookIssues = [];
    const cells = panel.content.widgets;
    const tempDiv = document.createElement('div');
    document.body.appendChild(tempDiv);
    try {
        // Create a complete heading structure that maps cell index to heading level and content
        // Use array to retain order of headings
        const headingStructure = [];
        // First pass: collect all headings
        for (let i = 0; i < cells.length; i++) {
            const cell = cells[i];
            if (!cell || !cell.model || cell.model.type !== 'markdown') {
                continue;
            }
            const content = cell.model.sharedModel.getSource();
            if (!content.trim()) {
                continue;
            }
            // Tokenize markdown and map tokens to source offsets for headings
            const tokens = marked__WEBPACK_IMPORTED_MODULE_0__.marked.lexer(content);
            let searchStart = 0;
            for (const token of tokens) {
                let level = null;
                let rawHeading = '';
                let text = '';
                if (token.type === 'heading') {
                    level = token.depth;
                    rawHeading = token.raw || '';
                    text = token.text || '';
                }
                else if (token.type === 'html') {
                    const rawHtml = token.raw || '';
                    const m = rawHtml.match(/<h([1-6])[^>]*>[\s\S]*?<\/h\1>/i);
                    if (m) {
                        level = parseInt(m[1], 10);
                        rawHeading = m[0];
                        text = rawHeading.replace(/<[^>]+>/g, '');
                    }
                }
                if (level !== null) {
                    // Bug Check: Is the rendered h1 really h1? (Markdown Setext-heading) -> Can be improved.
                    if (level === 1 &&
                        ((text || '').match(/(?<!\\)\$\$/g) || []).length === 1) {
                        continue;
                    }
                    const start = content.indexOf(rawHeading, searchStart);
                    if (start === -1) {
                        continue;
                    }
                    const end = start + rawHeading.length;
                    searchStart = end;
                    headingStructure.push({
                        cellIndex: i,
                        level,
                        content: text,
                        html: rawHeading,
                        offsetStart: start,
                        offsetEnd: end
                    });
                }
            }
        }
        // Track headings by level to detect duplicates
        // Only track h1 and h2 headings
        const h1Headings = new Map();
        const h2Headings = new Map();
        // First pass: collect all h1 and h2 headings
        headingStructure.forEach((heading, index) => {
            if (heading.level === 1) {
                const normalizedContent = heading.content.trim().toLowerCase();
                if (!h1Headings.has(normalizedContent)) {
                    h1Headings.set(normalizedContent, []);
                }
                h1Headings.get(normalizedContent).push(index);
            }
            else if (heading.level === 2) {
                const normalizedContent = heading.content.trim().toLowerCase();
                if (!h2Headings.has(normalizedContent)) {
                    h2Headings.set(normalizedContent, []);
                }
                h2Headings.get(normalizedContent).push(index);
            }
        });
        // Check for multiple h1 headings
        // First, find all h1 headings regardless of content
        const allH1Indices = headingStructure
            .map((heading, index) => (heading.level === 1 ? index : -1))
            .filter(index => index !== -1);
        // If there are multiple h1 headings, flag all but the first one
        if (allH1Indices.length > 1) {
            allH1Indices.slice(1).forEach(index => {
                const heading = headingStructure[index];
                notebookIssues.push({
                    cellIndex: heading.cellIndex,
                    cellType: 'markdown',
                    violationId: 'heading-multiple-h1',
                    issueContentRaw: heading.html,
                    metadata: {
                        headingStructure: headingStructure.filter(h => h.level === 1 || h.level === 2),
                        offsetStart: heading.offsetStart,
                        offsetEnd: heading.offsetEnd
                    }
                });
            });
        }
        // Check for duplicate h2 headings
        h2Headings.forEach((indices, content) => {
            if (indices.length > 1) {
                // Flag all h2 headings after the first one
                indices.slice(1).forEach(index => {
                    const heading = headingStructure[index];
                    notebookIssues.push({
                        cellIndex: heading.cellIndex,
                        cellType: 'markdown',
                        violationId: 'heading-duplicate-h2',
                        issueContentRaw: heading.html,
                        metadata: {
                            headingStructure: headingStructure.filter(h => h.level === 1 || h.level === 2),
                            offsetStart: heading.offsetStart,
                            offsetEnd: heading.offsetEnd
                        }
                    });
                });
            }
        });
        // Check for headings that appear in both h1 and h2
        h1Headings.forEach((h1Indices, content) => {
            if (h2Headings.has(content)) {
                // Flag all h2 headings that share content with h1
                h2Headings.get(content).forEach(index => {
                    const heading = headingStructure[index];
                    notebookIssues.push({
                        cellIndex: heading.cellIndex,
                        cellType: 'markdown',
                        violationId: 'heading-duplicate-h1-h2',
                        issueContentRaw: heading.html,
                        metadata: {
                            headingStructure: headingStructure.filter(h => h.level === 1 || h.level === 2),
                            offsetStart: heading.offsetStart,
                            offsetEnd: heading.offsetEnd
                        }
                    });
                });
            }
        });
        // Second pass: analyze heading structure for other issues
        for (let i = 0; i < headingStructure.length; i++) {
            const current = headingStructure[i];
            const previous = i > 0 ? headingStructure[i - 1] : null;
            // Check for empty headings
            if (!current.content.trim()) {
                notebookIssues.push({
                    cellIndex: current.cellIndex,
                    cellType: 'markdown',
                    violationId: 'heading-empty',
                    issueContentRaw: current.html,
                    metadata: {
                        offsetStart: current.offsetStart,
                        offsetEnd: current.offsetEnd
                    }
                });
            }
            // Skip first heading (no previous to compare with)
            if (!previous) {
                continue;
            }
            // Check for invalid heading level skips
            // Only flag violations when skipping to lower levels (e.g., h2 to h4)
            // Allow skips when returning to higher levels (e.g., h4 to h2)
            const levelDiff = current.level - previous.level;
            if (levelDiff > 1) {
                // Only check when going to lower levels
                notebookIssues.push({
                    cellIndex: current.cellIndex,
                    cellType: 'markdown',
                    violationId: 'heading-wrong-order',
                    issueContentRaw: current.html,
                    metadata: {
                        previousHeadingLevel: previous.level,
                        offsetStart: current.offsetStart,
                        offsetEnd: current.offsetEnd
                    }
                });
            }
        }
    }
    catch (error) {
        console.error('Error in heading hierarchy analysis:', error);
    }
    finally {
        tempDiv.remove();
    }
    return notebookIssues;
}


/***/ }),

/***/ "./lib/utils/detection/category/image.js":
/*!***********************************************!*\
  !*** ./lib/utils/detection/category/image.js ***!
  \***********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   detectImageIssuesInCell: () => (/* binding */ detectImageIssuesInCell)
/* harmony export */ });
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var tesseract_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! tesseract.js */ "webpack/sharing/consume/default/tesseract.js/tesseract.js");
/* harmony import */ var tesseract_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(tesseract_js__WEBPACK_IMPORTED_MODULE_1__);


async function getTextInImage(imagePath, currentDirectoryPath) {
    const worker = await tesseract_js__WEBPACK_IMPORTED_MODULE_1___default().createWorker('eng');
    try {
        const pathForTesseract = imagePath.startsWith('http')
            ? imagePath
            : `${_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__.PageConfig.getBaseUrl()}files/${currentDirectoryPath}/${imagePath}`;
        const { data: { text, confidence } } = await worker.recognize(pathForTesseract);
        if (!text) {
            throw new Error('No text found in the image');
        }
        return { text, confidence };
    }
    finally {
        await worker.terminate();
    }
}
async function detectImageIssuesInCell(rawMarkdown, cellIndex, cellType, notebookPath) {
    var _a, _b, _c;
    const notebookIssues = [];
    // Check for images without alt text in markdown syntax
    const mdSyntaxMissingAltRegex = /!\[\]\([^)]+\)/g;
    // Check for images without alt tag or empty alt tag in HTML syntax
    const htmlSyntaxMissingAltRegex = /<img[^>]*alt=["']\s*["'][^>]*\/?>/g;
    const htmlSyntaxNoAltRegex = /<img(?![^>]*alt=)[^>]*\/?>/g;
    // Iterate a list of regexes; each scans independently over the cell content
    const regexes = [
        mdSyntaxMissingAltRegex,
        htmlSyntaxMissingAltRegex,
        htmlSyntaxNoAltRegex
    ];
    for (const regex of regexes) {
        regex.lastIndex = 0;
        let match;
        while ((match = regex.exec(rawMarkdown)) !== null) {
            const imageUrl = ((_a = match[0].match(/\(([^)]+)\)/)) === null || _a === void 0 ? void 0 : _a[1]) ||
                ((_b = match[0].match(/src=["']([^"']+)["']/)) === null || _b === void 0 ? void 0 : _b[1]);
            if (!imageUrl) {
                continue;
            }
            const issueId = 'image-missing-alt';
            const start = (_c = match.index) !== null && _c !== void 0 ? _c : 0;
            const end = start + match[0].length;
            let suggestedFix = '';
            try {
                const ocrResult = await getTextInImage(imageUrl, notebookPath);
                if (ocrResult.confidence > 40) {
                    suggestedFix = ocrResult.text;
                }
            }
            catch (error) {
                console.error(`Failed to process image ${imageUrl}:`, error);
            }
            finally {
                notebookIssues.push({
                    cellIndex,
                    cellType: cellType,
                    violationId: issueId,
                    issueContentRaw: match[0],
                    suggestedFix: suggestedFix,
                    metadata: {
                        issueId: `cell-${cellIndex}-${issueId}-o${start}-${end}`,
                        offsetStart: start,
                        offsetEnd: end
                    }
                });
            }
        }
    }
    return notebookIssues;
}


/***/ }),

/***/ "./lib/utils/detection/category/link.js":
/*!**********************************************!*\
  !*** ./lib/utils/detection/category/link.js ***!
  \**********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   detectLinkIssuesInCell: () => (/* binding */ detectLinkIssuesInCell)
/* harmony export */ });
const VAGUE_PHRASES = ['click', 'here', 'link', 'more', 'read'];
const MIN_DESCRIPTIVE_CHARS = 20;
function isUrlLike(text) {
    const t = text.trim();
    return /^(https?:\/\/|www\.)/i.test(t);
}
function containsVaguePhrase(text) {
    const lower = text.toLowerCase();
    return VAGUE_PHRASES.some(p => lower.includes(p));
}
function extractAttr(tag, attr) {
    // Match attr='...' or attr="..."
    const m = new RegExp(attr + '=[\'"][^\'"]+[\'"]', 'i').exec(tag);
    return m
        ? m[0].split('=')[1].replace(/^['"]/, '').replace(/['"]$/, '')
        : null;
}
function detectLinkIssuesInCell(rawMarkdown, cellIndex, cellType) {
    var _a, _b;
    const issues = [];
    // Markdown links: [text](url)
    const mdLink = /\[([^\]]+)\]\(([^)\s]+)[^)]*\)/g;
    let match;
    while ((match = mdLink.exec(rawMarkdown)) !== null) {
        const full = match[0];
        const text = (match[1] || '').trim();
        const start = (_a = match.index) !== null && _a !== void 0 ? _a : 0;
        const end = start + full.length;
        const violation = shouldFlag(text);
        if (violation) {
            issues.push({
                cellIndex,
                cellType: cellType,
                violationId: 'link-discernible-text',
                issueContentRaw: full,
                metadata: {
                    issueId: `cell-${cellIndex}-link-discernible-text-o${start}-${end}`,
                    offsetStart: start,
                    offsetEnd: end
                }
            });
        }
    }
    // HTML links: <a ...>text</a>
    const htmlLink = /<a\b[^>]*>\s*([\s\S]*?)\s*<\/a>/gi;
    while ((match = htmlLink.exec(rawMarkdown)) !== null) {
        const full = match[0];
        const inner = (match[1] || '').replace(/<[^>]*>/g, '').trim();
        const tagStart = (_b = match.index) !== null && _b !== void 0 ? _b : 0;
        const tagEnd = tagStart + full.length;
        // Use aria-label if provided
        const openingTagMatch = /<a\b[^>]*>/i.exec(full);
        const openingTag = openingTagMatch ? openingTagMatch[0] : '';
        const aria = extractAttr(openingTag, 'aria-label');
        const label = aria && aria.trim() ? aria.trim() : inner;
        // Explicitly flag anchors with no discernible text and no aria-label
        const hasAria = !!(aria && aria.trim());
        const hasInnerText = inner.length > 0;
        if (!hasAria && !hasInnerText) {
            issues.push({
                cellIndex,
                cellType: cellType,
                violationId: 'link-discernible-text',
                issueContentRaw: full,
                metadata: {
                    issueId: `cell-${cellIndex}-link-discernible-text-o${tagStart}-${tagEnd}`,
                    offsetStart: tagStart,
                    offsetEnd: tagEnd
                }
            });
            continue;
        }
        const violation = shouldFlag(label);
        if (violation) {
            issues.push({
                cellIndex,
                cellType: cellType,
                violationId: 'link-discernible-text',
                issueContentRaw: full,
                metadata: {
                    issueId: `cell-${cellIndex}-link-discernible-text-o${tagStart}-${tagEnd}`,
                    offsetStart: tagStart,
                    offsetEnd: tagEnd
                }
            });
        }
    }
    return issues;
}
function shouldFlag(text) {
    // Flag if entire text is a URL
    if (isUrlLike(text)) {
        return true;
    }
    // AND condition: vague phrase present AND too short
    const tooShort = text.trim().length < MIN_DESCRIPTIVE_CHARS;
    const hasVague = containsVaguePhrase(text);
    return hasVague && tooShort;
}


/***/ }),

/***/ "./lib/utils/detection/category/table.js":
/*!***********************************************!*\
  !*** ./lib/utils/detection/category/table.js ***!
  \***********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   analyzeTableIssues: () => (/* binding */ analyzeTableIssues),
/* harmony export */   detectTableIssuesInCell: () => (/* binding */ detectTableIssuesInCell)
/* harmony export */ });
function detectTableIssuesInCell(rawMarkdown, cellIndex, cellType) {
    var _a, _b, _c;
    const notebookIssues = [];
    // Check for tables without th tags
    const tableWithoutThRegex = /<table[^>]*>(?![\s\S]*?<th[^>]*>)[\s\S]*?<\/table>/gi;
    let match;
    while ((match = tableWithoutThRegex.exec(rawMarkdown)) !== null) {
        const start = (_a = match.index) !== null && _a !== void 0 ? _a : 0;
        const end = start + match[0].length;
        notebookIssues.push({
            cellIndex,
            cellType: cellType,
            violationId: 'table-missing-header',
            issueContentRaw: match[0],
            metadata: {
                offsetStart: start,
                offsetEnd: end
            }
        });
    }
    // Check for tables without caption tags
    const tableWithoutCaptionRegex = /<table[^>]*>(?![\s\S]*?<caption[^>]*>)[\s\S]*?<\/table>/gi;
    while ((match = tableWithoutCaptionRegex.exec(rawMarkdown)) !== null) {
        const start = (_b = match.index) !== null && _b !== void 0 ? _b : 0;
        const end = start + match[0].length;
        notebookIssues.push({
            cellIndex,
            cellType: cellType,
            violationId: 'table-missing-caption',
            issueContentRaw: match[0],
            metadata: {
                offsetStart: start,
                offsetEnd: end
            }
        });
    }
    // Check for tables with th tags but missing scope attributes
    const tableWithThRegex = /<table[^>]*>[\s\S]*?<\/table>/gi;
    while ((match = tableWithThRegex.exec(rawMarkdown)) !== null) {
        const tableHtml = match[0];
        const start = (_c = match.index) !== null && _c !== void 0 ? _c : 0;
        const end = start + match[0].length;
        const parser = new DOMParser();
        const doc = parser.parseFromString(tableHtml, 'text/html');
        const table = doc.querySelector('table');
        if (table) {
            const thElements = table.querySelectorAll('th');
            let hasMissingScope = false;
            thElements.forEach(th => {
                if (!th.hasAttribute('scope')) {
                    hasMissingScope = true;
                }
            });
            if (hasMissingScope) {
                notebookIssues.push({
                    cellIndex,
                    cellType: cellType,
                    violationId: 'table-missing-scope',
                    issueContentRaw: tableHtml,
                    metadata: {
                        offsetStart: start,
                        offsetEnd: end
                    }
                });
            }
        }
    }
    return notebookIssues;
}
async function analyzeTableIssues(panel) {
    const notebookIssues = [];
    const cells = panel.content.widgets;
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        if (!cell || !cell.model || cell.model.type !== 'markdown') {
            continue;
        }
        const content = cell.model.sharedModel.getSource();
        if (!content.trim()) {
            continue;
        }
        const cellIssues = detectTableIssuesInCell(content, i, 'markdown');
        notebookIssues.push(...cellIssues);
    }
    return notebookIssues;
}


/***/ }),

/***/ "./lib/utils/edit.js":
/*!***************************!*\
  !*** ./lib/utils/edit.js ***!
  \***************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   getIssueOffsets: () => (/* binding */ getIssueOffsets),
/* harmony export */   replaceSlice: () => (/* binding */ replaceSlice)
/* harmony export */ });
function getIssueOffsets(issue, sourceLength) {
    var _a, _b, _c, _d;
    const start = (_b = (_a = issue.metadata) === null || _a === void 0 ? void 0 : _a.offsetStart) !== null && _b !== void 0 ? _b : null;
    const end = (_d = (_c = issue.metadata) === null || _c === void 0 ? void 0 : _c.offsetEnd) !== null && _d !== void 0 ? _d : null;
    if (start === null ||
        end === null ||
        isNaN(start) ||
        isNaN(end) ||
        start < 0 ||
        end > sourceLength ||
        start >= end) {
        return null;
    }
    return { offsetStart: start, offsetEnd: end };
}
function replaceSlice(source, start, end, replacement) {
    return source.slice(0, start) + replacement + source.slice(end);
}


/***/ }),

/***/ "./lib/utils/http.js":
/*!***************************!*\
  !*** ./lib/utils/http.js ***!
  \***************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   get: () => (/* binding */ get),
/* harmony export */   http: () => (/* binding */ http),
/* harmony export */   post: () => (/* binding */ post)
/* harmony export */ });
/* harmony import */ var axios__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! axios */ "webpack/sharing/consume/default/axios/axios");
/* harmony import */ var axios__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(axios__WEBPACK_IMPORTED_MODULE_0__);

function getDataUrlPayloadBytes(dataUrl) {
    // data:[<mediatype>][;base64],<data>
    const commaIdx = dataUrl.indexOf(',');
    if (commaIdx === -1) {
        return 0;
    }
    const header = dataUrl.substring(0, commaIdx).toLowerCase();
    const payload = dataUrl.substring(commaIdx + 1);
    if (header.includes(';base64')) {
        // Base64 size: 3/4 of length, minus padding
        const len = payload.length;
        const padding = payload.endsWith('==') ? 2 : payload.endsWith('=') ? 1 : 0;
        return Math.floor((len * 3) / 4) - padding;
    }
    // URL-encoded payload; approximate by decoding length
    try {
        return decodeURIComponent(payload).length;
    }
    catch (_a) {
        return payload.length;
    }
}
function enforceDataUrlLimit(url, cfg) {
    var _a;
    if (!url) {
        return;
    }
    if (url.startsWith('data:')) {
        const limit = (_a = cfg === null || cfg === void 0 ? void 0 : cfg.maxDataUrlBytes) !== null && _a !== void 0 ? _a : 10 * 1024 * 1024; // 10 MiB default
        const size = getDataUrlPayloadBytes(url);
        if (size > limit) {
            throw new Error(`Data URL exceeds limit (${size} bytes > ${limit} bytes)`);
        }
    }
}
async function get(url, config) {
    enforceDataUrlLimit(url, config);
    return axios__WEBPACK_IMPORTED_MODULE_0___default().get(url, config);
}
async function post(url, data, config) {
    enforceDataUrlLimit(url, config);
    return axios__WEBPACK_IMPORTED_MODULE_0___default().post(url, data, config);
}
const http = { get, post };


/***/ }),

/***/ "./lib/utils/metadata.js":
/*!*******************************!*\
  !*** ./lib/utils/metadata.js ***!
  \*******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   issueCategoryNames: () => (/* binding */ issueCategoryNames),
/* harmony export */   issueToCategory: () => (/* binding */ issueToCategory),
/* harmony export */   issueToDescription: () => (/* binding */ issueToDescription)
/* harmony export */ });
const issueCategoryNames = [
    'Images',
    'Headings',
    'Lists',
    'Tables',
    'Color',
    'Links',
    'Other'
];
const issueToCategory = new Map([
    // 1. Images
    ['image-missing-alt', 'Images'],
    // TODO: 2. Headings
    ['heading-missing-h1', 'Headings'],
    ['heading-multiple-h1', 'Headings'],
    ['heading-duplicate', 'Headings'],
    ['heading-duplicate-h2', 'Headings'],
    ['heading-duplicate-h1-h2', 'Headings'],
    ['heading-wrong-order', 'Headings'],
    ['heading-empty', 'Headings'],
    // TODO: 3. Tables
    ['table-missing-header', 'Tables'],
    ['table-missing-caption', 'Tables'],
    ['table-missing-scope', 'Tables'],
    // TODO: 4. Color
    ['color-insufficient-cc-normal', 'Color'],
    ['color-insufficient-cc-large', 'Color'],
    // TODO: Lists
    // TODO: Links
    ['link-discernible-text', 'Links']
    // TODO: Other
]);
const issueToDescription = new Map([
    // 1. Images
    [
        'image-missing-alt',
        {
            title: 'Missing Alt Text',
            description: 'All images must have alternate text to convey their purpose and meaning to screen reader users.',
            detailedDescription: "Ensure all informative images have short, descriptive alternate text. Screen readers have no way of translating an image into words that gets read to the user, even if the image only consists of text. As a result, it's necessary for images to have short, descriptive alt text so screen reader users clearly understand the image's contents and purpose",
            descriptionUrl: 'https://dequeuniversity.com/rules/axe/4.4/image-alt'
        }
    ],
    // TODO: 2. Headings
    [
        'heading-missing-h1',
        {
            title: 'Missing H1 Heading',
            description: 'Ensure a single H1 tag is present at the top of the notebook.',
            detailedDescription: 'Screen reader users can use keyboard shortcuts to navigate directly to the first h1, which, in principle, should allow them to jump directly to the main content of the web page. If there is no h1, or if the h1 appears somewhere other than at the start of the main content, screen reader users must listen to more of the web page to understand its structure, making the experience confusing and frustrating. Please also ensure that headings contain descriptive, accurate text',
            descriptionUrl: 'https://dequeuniversity.com/rules/axe/4.1/page-has-heading-one'
        }
    ],
    [
        'heading-multiple-h1',
        {
            title: 'Duplicate H1 Heading',
            description: 'Ensure there is only one level-one heading (h1) in the notebook.',
            detailedDescription: 'The h1 heading should be at the top of the document and serve as the main title. Additional h1 headings can confuse screen reader users about the document structure. Please also ensure that headings contain descriptive, accurate text'
        }
    ],
    [
        'heading-duplicate-h2',
        {
            title: 'Duplicate Heading h2',
            description: 'Ensure identical h2 headings are not used.',
            detailedDescription: 'This can be confusing for screen reader users as it creates redundant landmarks in the document structure. Please consider combining the sections or using different heading text'
        }
    ],
    [
        'heading-duplicate-h1-h2',
        {
            title: 'Duplicate Heading h1 and h2',
            description: 'Ensure h1 and h2 headings do not share the same text.',
            detailedDescription: 'This can be confusing for screen reader users as it creates redundant landmarks in the document structure. Please use different text for h1 and h2 headings'
        }
    ],
    [
        'heading-wrong-order',
        {
            title: 'Wrong Heading Order',
            description: 'Headings must be in a valid logical order, meaning H1 through H6 element tags must appear in a sequentially-descending order.',
            detailedDescription: 'Ensure the order of headings is semantically correct. Headings provide essential structure for screen reader users to navigate a page. Skipping levels or using headings out of order can make the content feel disorganized or inaccessible. Please also ensure that headings contain descriptive, accurate text',
            descriptionUrl: 'https://dequeuniversity.com/rules/axe/pdf/2.0/heading-order'
        }
    ],
    [
        'heading-empty',
        {
            title: 'Empty Heading',
            description: 'Ensure that a heading element contains content.',
            detailedDescription: 'Ensure headings have discernible text. Headings provide essential structure for screen reader users to navigate a page. When a heading is empty, it creates confusion and disrupts this experience. Please also ensure that headings contain descriptive, accurate text',
            descriptionUrl: 'https://dequeuniversity.com/rules/axe/4.2/empty-heading'
        }
    ],
    // TODO: 3. Tables
    [
        'table-missing-header',
        {
            title: 'Missing Table Header',
            description: 'Ensure that a table has a row, column, or both headers.',
            detailedDescription: 'Tables must have header cells to provide context for the data. Without headers, screen reader users cannot understand the relationship between data cells and their meaning. Please add appropriate header cells using the <th> tag'
        }
    ],
    [
        'table-missing-caption',
        {
            title: 'Missing Table Caption',
            description: 'Ensure that a table has a caption.',
            detailedDescription: 'Tables should have captions to provide a brief description of their content. Captions help screen reader users understand the purpose and context of the table data. Please add a caption using the <caption> tag'
        }
    ],
    [
        'table-missing-scope',
        {
            title: 'Missing Table Scope',
            description: 'Ensure that a table has a scope attribute.',
            detailedDescription: 'Table headers must have scope attributes'
        }
    ],
    // TODO: 4. Color
    [
        'color-insufficient-cc-normal',
        {
            title: 'Insufficient Color Contrast',
            description: 'Ensure that a text in an image has sufficient color contrast.',
            detailedDescription: 'Text must have sufficient contrast with its background to be readable. For normal text, the contrast ratio should be at least 4.5:1. This ensures that users with visual impairments can read the content',
            descriptionUrl: 'https://dequeuniversity.com/rules/axe/3.5/color-contrast'
        }
    ],
    [
        'color-insufficient-cc-large',
        {
            title: 'Insufficient Color Contrast',
            description: 'Ensure that a large text in an image has sufficient color contrast.',
            detailedDescription: 'Large text must have sufficient contrast with its background to be readable. For large text (18pt or 14pt bold), the contrast ratio should be at least 3:1. This ensures that users with visual impairments can read the content',
            descriptionUrl: 'https://dequeuniversity.com/rules/axe/3.5/color-contrast'
        }
    ],
    // TODO: Lists
    // TODO: Links
    [
        'link-discernible-text',
        {
            title: 'Link Text Not Descriptive',
            description: 'Links must have discernible, descriptive text (or aria-label) that conveys purpose without relying on surrounding context.',
            detailedDescription: 'Avoid vague phrases like "click here" or bare URLs. Provide concise, meaningful link text that describes the destination. This helps all users, including screen reader users, understand link purpose.',
            descriptionUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html'
        }
    ]
    // TODO: Other
]);


/***/ })

}]);
//# sourceMappingURL=lib_index_js.04d3d5a7a22a0e35f657.js.map