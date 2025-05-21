import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

/**
 * Custom slider made by raumen and laurod
 *
 * @export
 * @class SliderComponent
 * @typedef {SliderComponent}
 * @implements {OnInit}
 * @implements {OnChanges}
 */
@Component({
  selector: 'sliderlautups',
  templateUrl: './slider.component.html',
  styleUrls: ['./slider.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SliderComponent implements OnInit, OnChanges {

  /**
   * Initial value from slider
   *
   * @type {number}
   */
  @Input() initialValue: number = 50;
  /**
   * if the slider need steps and the number of it
   *
   * @type {?number}
   */
  @Input() step?: number;
  /**
   * min value from slider
   *
   * @type {number}
   */
  @Input() min: number = 0;
  /**
   * max value from slider
   *
   * @type {number}
   */
  @Input() max: number = 100;
  /**
   * show units from slider
   *
   * @type {boolean}
   */
  @Input() showUnits: boolean = true;
  /**
   * units value
   *
   * @type {string}
   */
  @Input() units: string = '%';
  /**
   * custom unit value
   *
   * @type {?() => string}
   */
  @Input() unitsValue?: () => string;
  /**
   * bring the new value
   *
   * @type {*}
   */
  @Output() changeValue = new EventEmitter();

  /**
   * fromgroup
   *
   * @type {FormGroup}
   */
  form: FormGroup = new FormGroup({});
  /**
   * dragging value
   *
   * @type {boolean}
   */
  isActive = false;
  /**
   * Creates an instance of SliderComponent.
   *
   * @constructor
   * @param {FormBuilder} formBuilder
   */
  constructor(
    private formBuilder: FormBuilder,
  ) { }

  /**
   * Valid if the initalValue changes
   *
   * @param {SimpleChanges} changes
   */
  ngOnChanges(changes: SimpleChanges): void {
    if (changes["initialValue"]) {
      this.calcularBarra(this.initialValue);
    }
  }

  /**
   *
   */
  ngOnInit() {
    this.setForm();
    this.calcularBarra(this.initialValue);
  }

  /**
   *
   * @public
   */
  public setForm() {
    this.form = this.formBuilder.group({
      sliderValue: [this.initialValue, Validators.required],

    });
    this.form.controls['sliderValue'].valueChanges.subscribe((res) => this.actualizarSlider(res))
  }

  /**
   * update slider value and emit the new value
   *
   * @public
   * @param {number} res
   */
  public actualizarSlider(res: number) {
    setTimeout(() => {
    this.changeValue.next(res);
    });
    this.calcularBarra(res);
  }

  /**
   * calculate the percentage of the slider 
   *
   * @param {number} number
   * @returns {number}
   */
  calcularPorcentaje(number: number): number {
    return ((number - this.min) / (this.max - this.min)) * 100;
  }

  /**
   * return the percentage of slider to color it
   *
   * @param {number} value
   */
  calcularBarra(value: number) {
    if (this.min === 0 && this.max === 100) {
      document.documentElement.style.setProperty('--slider-style', `${value}%`)
      document.documentElement.style.setProperty('--slider-gray-style', `${value + 1}%`)
    } else {
      const porcentaje = this.calcularPorcentaje(value);
      document.documentElement.style.setProperty('--slider-style', `${porcentaje}%`)
      document.documentElement.style.setProperty('--slider-gray-style', `${porcentaje + 1}%`)
    }
  }

  /**
   * Activate dragging cursor
   */
  activateDragging(): void {
    this.isActive = true;
  }

  /**
   * desactivate dragging cursor
   */
  deactivateDragging(): void {
    this.isActive = false;
  }

}
