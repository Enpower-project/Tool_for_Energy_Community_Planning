import { Component, ElementRef, EventEmitter, HostListener, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'multiple-selectups',
  templateUrl: './multiple-select.component.html',
  styleUrls: ['./multiple-select.component.scss']
})
export class MultipleSelectComponent implements OnInit, OnChanges {

  @Input() title?: string;
  @Input() options: any;
  @Input() selectedIndex: number[] = [];
  @Input() hint?: string;
  @Input() disabled: boolean = false;
  @Input() showChevron: boolean = true;
  @Input() inputString: string = "Select Option";
  @Input() selectedvalue?: any;
  @Input() addNewValues: boolean = false;
  @Output() AddNewValue = new EventEmitter();
  @Output() changeValue = new EventEmitter();

  public openSelect: boolean = false;

  constructor(
    private eRef: ElementRef,
    private formBuilder: FormBuilder) { }

  form: FormGroup = new FormGroup({});

  ngOnInit() {
    this.setForm();
    this.setInitialValues();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['selectedvalue']) {
      this.setInitialValues();
    }
  }

  public setInitialValues() {
    let array = [];
    if (this.selectedvalue) {
      for (let index = 0; index < this.options.length; index++) {
        if (this.selectedvalue.find((value: any) => value === this.options[index])) {
          array.push(index)
        }
      }
    }
    this.selectedIndex = array;
  }

  public setForm() {
    this.form = this.formBuilder.group({
      newMember: ["", Validators.required],
    });
  }

  public selectOption(index: number) {
    if (this.selectedIndex?.find((pos) => pos === index) !== undefined) {
      this.selectedIndex = this.selectedIndex.filter((pos) => pos !== index);;
    } else {
      this.selectedIndex?.push(index);
    }

    this.changeValue.next(this.getArrayValues());
  }

  public show() {
    if (!this.disabled) {
      this.openSelect = !this.openSelect;
    }
  }

  @HostListener('document:click', ['$event'])
  public clickFuera(event: any) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.openSelect = false;
    }
  }

  public isChecked(index: number) {
    return this.selectedIndex?.find((pos) => pos === index) !== undefined;
  }

  public save() {
    const newMember = this.form.controls["newMember"].value;
    if (newMember) {
      this.form.controls["newMember"].setValue("");
      const newArray = this.options.push(newMember);
      this.AddNewValue.next(newArray);
    }
  }

  public getArrayValues() {
    let values: any = [];

    this.selectedIndex.forEach(index => {
      values.push(this.options[index])
    });

    return values;
  }

  // preventCheck(event: MouseEvent, index:number): void {
  //   event.preventDefault();
  //   event.stopPropagation();
  //   this.selectOption(index);
  // }

}
