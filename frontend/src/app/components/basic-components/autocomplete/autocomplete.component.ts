import { Component, ElementRef, EventEmitter, HostListener, Input, OnInit, Output, ViewChild } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';


@Component({
  selector: 'autocompletups',
  templateUrl: './autocomplete.component.html',
  styleUrls: ['./autocomplete.component.scss']
})
export class AutocompleteComponent implements OnInit {

  @Input() title?: string;
  @Input() options: any = [];
  @Input() selectedIndex?: number;
  @Input() hint?: string;
  @Input() disabled: boolean = false;
  @Input() showChevron: boolean = true;
  @Input() placeHolder: string = "BASELINE.LOCATION.SEARCH_LOCATION";
  @Input() icon: string = "search.svg";
  @Input() selectedvalue?: any;
  @Input() initialValue: string = "";
  @Input() loading: boolean = false;
  @Input() noData: boolean = false;
  @Output() changeValue = new EventEmitter()
  form: FormGroup = new FormGroup({});

  public openSelect: boolean = false;

  constructor(
    private eRef: ElementRef,
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit(): void {
    this.setForm()
  }

  public selectOption(index: number) {
    this.selectedIndex = index;
    this.openSelect = false;
    this.changeValue.next(index);
  }

  public show() {
    if (!this.disabled) {
      this.openSelect = !this.openSelect;
    }
  }

  public setForm() {
    this.form = this.formBuilder.group({
      valor: [this.initialValue, Validators.required],
    });
    this.form.controls['valor'].valueChanges.subscribe((res) => this.changeValue.next(res))
  }

  @HostListener('document:click', ['$event'])
  public clickFuera(event: any) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.openSelect = false;
    }
  }

}
