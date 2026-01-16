" ═══════════════════════════════════════════════════════════════
" Zolo Default - Vim Color Scheme
" ═══════════════════════════════════════════════════════════════
" Default color scheme for .zolo files with LSP semantic tokens
" Version: 1.0.0
" Author: Zolo Media
" Generated automatically from zlsp/themes/zolo_default.yaml
" DO NOT EDIT - Changes will be overwritten!
" ═══════════════════════════════════════════════════════════════

" Clear conflicting default syntax groups
highlight! Identifier gui=NONE cterm=NONE
highlight! Keyword gui=NONE cterm=NONE
highlight! Constant gui=NONE cterm=NONE
highlight! Special gui=NONE cterm=NONE

" Semantic token highlights
" Top-level keys (app_name, server, features)
highlight! LspSemanticRootKey ctermfg=216 guifg=#ffaf87 cterm=NONE gui=NONE term=NONE

" Nested keys (host, port, ssl)
highlight! LspSemanticNestedKey ctermfg=222 guifg=#ffd787 cterm=NONE gui=NONE term=NONE

" zMeta in zUI/zSchema files, zVaF and component name in zUI files (Zolo convention root keys)
highlight! LspSemanticZmetaKey ctermfg=114 guifg=#87d787 cterm=NONE gui=NONE term=NONE

" zKernel zData keys under zMeta in zSchema.*.zolo files (Data_Type, Data_Label, Data_Source, Schema_Name, zMigration, zMigrationVersion)
highlight! LspSemanticZkernelDataKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE

" Field property keys in zSchema.*.zolo files (type, pk, auto_increment, unique, required, default, rules, zHash, comment, format, min_length, max_length, pattern, min, max)
highlight! LspSemanticZschemaPropertyKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE

" Bifrost underscore keys (_zClass, _zId) in zUI.*.zolo files
highlight! LspSemanticBifrostKey ctermfg=51 guifg=#00ffff cterm=NONE gui=NONE term=NONE

" UI element keys (zImage, zText, zURL, zH1-zH6, zNavBar, zUL) in zUI.*.zolo files
highlight! LspSemanticUiElementKey ctermfg=202 guifg=#ff5f00 cterm=NONE gui=NONE term=NONE

" zSpark root key in zSpark.*.zolo files
highlight! LspSemanticZsparkKey ctermfg=114 guifg=#87d787 cterm=NONE gui=NONE term=NONE

" Config root keys in zEnv.*.zolo files (DEPLOYMENT, DEBUG, LOG_LEVEL)
highlight! LspSemanticZenvConfigKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE

" First-level nested keys under ZNAVBAR in zEnv files (not grandchildren)
highlight! LspSemanticZnavbarNestedKey ctermfg=208 guifg=#ff8700 cterm=NONE gui=NONE term=NONE

" zSub key in zEnv/zUI files at grandchild+ level (indent >= 4)
highlight! LspSemanticZsubKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE

" zRBAC access control key in zEnv/zUI files (child of any key)
highlight! LspSemanticZrbacKey ctermfg=196 guifg=#ff0000 cterm=NONE gui=NONE term=NONE

" zKey modifiers (^, ~, !, *) in zEnv/zUI files
highlight! LspSemanticZrbacOptionKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE

" z-prefixed root keys in zConfig.*.zolo files (e.g., zMachine)
highlight! LspSemanticZconfigKey ctermfg=114 guifg=#87d787 cterm=NONE gui=NONE term=NONE

" User-editable nested keys under zMachine (preferences, limits)
highlight! LspSemanticZmachineEditableKey ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE

" Auto-detected locked nested keys under zMachine (hardware, system)
highlight! LspSemanticZmachineLockedKey ctermfg=160 guifg=#d70000 cterm=NONE gui=NONE term=NONE

" All nested keys under zSpark root in zSpark files
highlight! LspSemanticZsparkNestedKey ctermfg=98 guifg=#875fd7 cterm=NONE gui=NONE term=NONE

" zMode value (Terminal/zBifrost) in zSpark files - tomato red
highlight! LspSemanticZsparkModeValue ctermfg=196 guifg=#ff0000 cterm=NONE gui=NONE term=NONE

" zVaFile value (zUI.*) in zSpark files - dark green
highlight! LspSemanticZsparkVaFileValue ctermfg=40 guifg=#00d700 cterm=NONE gui=NONE term=NONE

" zBlock value in zSpark files - salmon orange
highlight! LspSemanticZsparkSpecialValue ctermfg=216 guifg=#ffaf87 cterm=NONE gui=NONE term=NONE

" Environment/config constants (PROD, DEBUG, INFO, etc.)
highlight! LspSemanticEnvConfigValue ctermfg=226 guifg=#ffff00 cterm=NONE gui=NONE term=NONE

" String values
highlight! LspSemanticString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Version numbers (1.0.0, 2.1.3-beta)
highlight! LspSemanticVersionString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Time values (14:30:00, 09:15:30)
highlight! LspSemanticTimeString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Timestamp values (2024-01-06T14:30:00)
highlight! LspSemanticTimestampString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Ratio values (16:9, 4:3, 21:9)
highlight! LspSemanticRatioString ctermfg=230 guifg=#fffbcb cterm=NONE gui=NONE term=NONE

" Numeric values (8080, 100, 3.14)
highlight! LspSemanticNumber ctermfg=214 guifg=#FF8C00 cterm=NONE gui=NONE term=NONE

" Escape sequences (\n, \t, \", \\, \uXXXX)
highlight! LspSemanticEscapeSequence ctermfg=196 guifg=#ff0000 cterm=NONE gui=NONE term=NONE

" Type hint text (int, bool, float, str)
highlight! LspSemanticTypeHint ctermfg=141 guifg=#af87ff cterm=NONE gui=NONE term=NONE

" Type hint parentheses ( )
highlight! LspSemanticTypeHintParen ctermfg=227 guifg=#ffff5f cterm=NONE gui=NONE term=NONE

" Array/list brackets [ ]
highlight! LspSemanticBracketStructural ctermfg=159 guifg=#afffff cterm=NONE gui=NONE term=NONE

" Object/dict braces { }
highlight! LspSemanticBraceStructural ctermfg=165 guifg=#d700ff cterm=NONE gui=NONE term=NONE

" Brackets [ ] inside string values
highlight! LspSemanticStringBracket ctermfg=159 guifg=#afffff cterm=NONE gui=NONE term=NONE

" Braces { } inside string values
highlight! LspSemanticStringBrace ctermfg=165 guifg=#d700ff cterm=NONE gui=NONE term=NONE

" Boolean values (true, false)
highlight! LspSemanticBoolean ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE

" Null values (null)
highlight! LspSemanticNull ctermfg=33 guifg=#0087ff cterm=NONE gui=NONE term=NONE

" zPath values (@.logs, ~.config) in zKernel files
highlight! LspSemanticZpathValue ctermfg=51 guifg=#00ffff cterm=NONE gui=NONE term=NONE

" Comments
highlight! LspSemanticComment ctermfg=242 guifg=#6c6c6c cterm=italic gui=italic term=NONE

" ═══════════════════════════════════════════════════════════════
" Color Palette Reference
" ═══════════════════════════════════════════════════════════════
" 216 - #ffaf87 - Salmon Orange        Warm orange for hierarchy markers
" 222 - #ffd787 - Golden Yellow        Golden yellow for nested elements
" 230 - #fffbcb - Light Cream          Soft cream for text content
" 214 - #FF8C00 - Dark Orange          Vibrant orange for numeric values
" 141 - #af87ff - Light Purple         Light purple for type information
" 227 - #ffff5f - Soft Yellow          Soft yellow for structural elements
" 159 - #afffff - Light Cyan           Light cyan for brackets and dashes
"  33 - #0087ff - Deep Blue            Deep blue for boolean values
"  20 - #0000d7 - Test Blue            Test color for ZNAVBAR nested keys
" 208 - #ff8700 - Dark Orange          Dark orange for ZNAVBAR nested keys
" 242 - #6c6c6c - Gray                 Muted gray for comments
" 165 - #d700ff - Magenta              Bright magenta for object braces
" 196 - #ff0000 - Bright Red           Bright red for escape sequences
" 160 - #d70000 - Dark Red             Dark red for locked/restricted items
" 114 - #87d787 - Light Green          Light green for zSpark root key
"  98 - #875fd7 - Purple               Purple for zPath values
"  40 - #00d700 - Dark Green           Dark green for zSpark special keys
"  99 - #875fff - Light Purple         Light purple for zSpark special values
"  51 - #00ffff - Bright Cyan          Bright cyan for zPath values
" 226 - #ffff00 - Bright Yellow        Bright yellow for environment/config constants
" 202 - #ff5f00 - Orange Red           Orange-red for UI element keys
" ═══════════════════════════════════════════════════════════════