import { Component, Input, OnInit } from '@angular/core';

/**
 * separator made by raumen
 *
 * @export
 * @class SeparatorComponent
 * @typedef {SeparatorComponent}
 */
@Component({
  selector: 'separatups',
  templateUrl: './separator.component.html',
  styleUrls: ['./separator.component.scss']
})
export class SeparatorComponent {

  /**
   * if separator have the word "or" in the midle
   *
   * @type {boolean}
   */
  @Input() orSeparator: boolean = false;
  @Input() isBlueSeparator: boolean = false;
  /**
   * separator or text 
   *
   * @type {string}
   */
  @Input() text: string = "NAVIGATION.OR";


  /**
   * Creates an instance of SeparatorComponent.
   *
   * @constructor
   */
  constructor() { }

}
