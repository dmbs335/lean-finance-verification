import Lake
open Lake DSL

package leanFinanceVerification where
  version := v!"0.1.0"

@[default_target]
lean_lib LeanFinance

lean_exe leanFinance where
  root := `Main
