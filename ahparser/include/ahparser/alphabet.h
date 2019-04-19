/**
 * file:         alphabet.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  ABNF alphabet
 */

#ifndef AHPARSER_ALPHABET_H_
#define AHPARSER_ALPHABET_H_

typedef unsigned char ahp_alphabet_t[256];

extern const ahp_alphabet_t AHP_RULES_CHAR;
extern const ahp_alphabet_t AHP_RULES_UPALPHA;
extern const ahp_alphabet_t AHP_RULES_LOALPHA;
extern const ahp_alphabet_t AHP_RULES_ALPHA;
extern const ahp_alphabet_t AHP_RULES_DIGIT;
extern const ahp_alphabet_t AHP_RULES_CTLS;
extern const ahp_alphabet_t AHP_RULES_HTSP;
extern const ahp_alphabet_t AHP_RULES_LWS;
extern const ahp_alphabet_t AHP_RULES_SEPARATORS;
extern const ahp_alphabet_t AHP_RULES_TOKEN;
extern const ahp_alphabet_t AHP_RULES_FVCHAR;
extern const ahp_alphabet_t AHP_RULES_TEXT;
extern const ahp_alphabet_t AHP_RULES_HEX;
extern const ahp_alphabet_t AHP_RULES_URL;

#define AHP_RULES_HT 9    // \t
#define AHP_RULES_LF 10   // \n
#define AHP_RULES_CR 13   // \r
#define AHP_RULES_SP 32   // ' '
#define AHP_RULES_DQ 34   // "
#define AHP_RULES_DOT 46  // .

#endif  // AHPARSER_ALPHABET_H_
