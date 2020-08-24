/**
 * file:         alphabet.h
 * author:       James Yin<ywhjames@hotmail.com>
 * description:  ABNF alphabet
 */
#ifndef AHPARSER_ALPHABET_H_
#define AHPARSER_ALPHABET_H_

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef bool ahp_alphabet_t[256];

extern const ahp_alphabet_t AHP_RULES_VCHAR;
extern const ahp_alphabet_t AHP_RULES_TCHAR;
extern const ahp_alphabet_t AHP_RULES_HEX;
extern const ahp_alphabet_t AHP_RULES_HTSP;
extern const ahp_alphabet_t AHP_RULES_QDTEXT;
extern const ahp_alphabet_t AHP_RULES_ETEXT;
extern const ahp_alphabet_t AHP_RULES_FLOD;
extern const ahp_alphabet_t AHP_RULES_URL;

#define AHP_RULES_HT 9    // \t
#define AHP_RULES_LF 10   // \n
#define AHP_RULES_CR 13   // \r
#define AHP_RULES_SP 32   // ' '
#define AHP_RULES_DQ 34   // "
#define AHP_RULES_DOT 46  // .

#ifdef __cplusplus
}
#endif

#endif  // AHPARSER_ALPHABET_H_
