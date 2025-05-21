import { Component, ElementRef, EventEmitter, HostListener, Input, Output } from '@angular/core';

/**
 * Custom slider made by raumen
 *
 * @export
 * @class SelectComponent
 * @typedef {SelectComponent}
 * @implements {OnInit}
 */
@Component({
  selector: 'selectups',
  templateUrl: './select.component.html',
  styleUrls: ['./select.component.scss']
})
export class SelectComponent {

  /**
   * Text at the top of the selector
   *
   * @type {?string}
   */
  @Input() title?: string;
  /**
   * List of names with options
   *
   * @type {*}
   */
  @Input() options: any;
  /**
   * Position of selected name
   *
   * @type {?number}
   */
  @Input() selectedIndex?: number;
  /**
   * Text at the bottom of the selector
   *
   * @type {?string}
   */
  @Input() hint?: string;
  /**
   * Valid if select is disabled
   *
   * @type {boolean}
   */
  @Input() disabled: boolean = false;
  /**
   * Valid if it shows the chevron
   *
   * @type {boolean}
   */
  @Input() showChevron: boolean = true;
  /**
   * Placeholder
   *
   * @type {string}
   */
  @Input() inputString: string = "Select Option";
  /**
   * returns the selected value
   *
   * @type {*}
   */
  @Output() changeValue = new EventEmitter()

  /**
   * open modal with the options
   *
   * @public
   * @type {boolean}
   */
  public openSelect: boolean = false;

  /**
   * Creates an instance of SelectComponent.
   *
   * @constructor
   * @param {ElementRef} eRef
   */
  constructor(private eRef: ElementRef) { }

  /**
   * Description placeholder
   *
   * @public
   * @param {number} index
   */
  public selectOption(index: number) {
    this.selectedIndex = index;
    this.openSelect = false;
    this.changeValue.next(index);
  }

  /**
   * Open or Close the modal
   *
   * @public
   */
  public show() {
    if (!this.disabled) {
      this.openSelect = !this.openSelect;
    }
  }

  /**
   * Close the modal with options if you click outside the component
   *
   * @public
   * @param {*} event
   */
  @HostListener('document:click', ['$event'])
  public clickFuera(event: any) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.openSelect = false;
    }
  }

}
