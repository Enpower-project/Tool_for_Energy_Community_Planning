import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-slider-component',
  templateUrl: './slider-component.component.html',
  styleUrls: ['./slider-component.component.scss']
})
export class SliderComponentComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();

  form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
  ) { }


  ngOnInit() {
    this.setForm();
    document.documentElement.style.setProperty('--slider-style', `${50}%`);
    document.documentElement.style.setProperty('--slider-gray-style', `${51}%`)
  }

  public setForm() {
    this.form = this.formBuilder.group({
      sliderValue: [50, Validators.required],

    });
    this.form.controls['sliderValue'].valueChanges.subscribe((res) => this.actualizarSlider(res))
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public goNext() {
    this.next.emit();
  }

  public actualizarSlider(res: number) {
    document.documentElement.style.setProperty('--slider-style', `${res}%`)
    document.documentElement.style.setProperty('--slider-gray-style', `${res + 1}%`)

  }

}
