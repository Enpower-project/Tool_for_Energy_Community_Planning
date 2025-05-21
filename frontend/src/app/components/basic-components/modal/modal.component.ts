import { Component, Input } from '@angular/core';

/**
 * Custom modal made by raumen
 *
 * @export
 * @class ModalComponent
 * @typedef {ModalComponent}
 */
@Component({
  selector: 'modalitups',
  templateUrl: './modal.component.html',
  styleUrls: ['./modal.component.scss']
})
export class ModalComponent {

  /**
   * Valid if the modal is open
   *
   * @type {boolean}
   */
  @Input() isOpen: boolean = false;
  /**
   * Change if the modal have the position absolute or fixed 
   *
   * @type {boolean}
   */
  @Input() isAbsolute: boolean = false;
  /**
   * Shows a div with white backgrounf on the center
   *
   * @type {boolean}
   */
  @Input() showBox: boolean = true;
  /**
   * change between darkness background
   *
   * @type {boolean}
   */
  @Input() lightBackground: boolean = false;

  @Input() background: boolean = true;

  @Input() fadeDown: boolean = false;


  /**
   * Creates an instance of ModalComponent.
   *
   * @constructor
   */
  constructor() { }
}
