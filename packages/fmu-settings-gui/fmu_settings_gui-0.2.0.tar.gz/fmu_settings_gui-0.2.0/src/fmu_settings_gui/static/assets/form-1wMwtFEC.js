import{d as f,r as x,j as e,y as g}from"./index-Cxh88Jww.js";import{h as E,c as F,T,f as b,a as S,S as h,G as y,C as D,i as R}from"./validator-DIfk4gqH.js";const k=f.div`
  form > div {
    margin-bottom: 1em;
  }

  button + button {
    margin-left: 8px;
  }
`,V=f.div`
  display: flex;
  gap: 8px;
`,{useAppForm:G}=F({fieldContext:b,formContext:S,fieldComponents:{TextField:T},formComponents:{CancelButton:D,GeneralButton:y,SubmitButton:h}});function O({name:s,label:a,value:i,placeholder:l,helperText:n,length:o,minLength:d,mutationCallback:j,mutationIsPending:C}){const[p,u]=x.useState(!0),[v,A]=x.useState(!0),c=E({length:o,minLength:d}),B=({message:t,formReset:m})=>{g.info(t),m(),u(!0)},r=G({defaultValues:{[s]:i},onSubmit:({formApi:t,value:m})=>{j({formValue:m,formSubmitCallback:B,formReset:t.reset})}});return e.jsx(k,{children:e.jsxs("form",{onSubmit:t=>{t.preventDefault(),t.stopPropagation(),r.handleSubmit()},children:[e.jsx(r.AppField,{name:s,...c&&{validators:{onBlur:c}},children:t=>e.jsx(t.TextField,{label:a,placeholder:l,helperText:n,isReadOnly:p,setSubmitDisabled:A})}),e.jsx(r.AppForm,{children:p?e.jsx(r.GeneralButton,{label:"Edit",onClick:()=>{u(!1)}}):e.jsxs(e.Fragment,{children:[e.jsx(r.SubmitButton,{label:"Save",disabled:v,isPending:C}),e.jsx(r.CancelButton,{onClick:t=>{t.preventDefault(),r.reset(),u(!0)}})]})})]})})}const{useAppForm:P}=F({fieldContext:b,formContext:S,fieldComponents:{SearchField:R},formComponents:{SubmitButton:h}});function U({name:s,value:a,helperText:i,setStateCallback:l}){const n=P({defaultValues:{[s]:a},onSubmit:({formApi:o,value:d})=>{l(d[s]),o.reset()}});return e.jsx("form",{onSubmit:o=>{o.preventDefault(),o.stopPropagation(),n.handleSubmit()},children:e.jsxs(V,{children:[e.jsx(n.AppField,{name:s,children:o=>e.jsx(o.SearchField,{helperText:i,toUpperCase:!0})}),e.jsx(n.AppForm,{children:e.jsx(n.SubmitButton,{label:"Search"})})]})})}export{O as E,U as S};
