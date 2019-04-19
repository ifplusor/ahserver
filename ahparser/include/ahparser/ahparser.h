/**
 * file: ahp.h
 * author: James Yin<ywhjames@hotmail.com>
 * description:
 *
 *   ahparser 是为 async io 设计的 http 报文解析器。ahparser 只专注于报文解析，
 *   使用 delegate 模式解耦 http 协议处理职责，使用状态机机制支持异步模式下网络 io 与解析运算的交错运行。
 *
 */

/*
 * API 约定:
 *   所有以 ahp_ 作为前缀的函数，都以 errno 作为返回值;
 *   所有不以 ahp_ 作为前缀的解码函数，失败后不应产生副作用;
 *
 * API 返回值说明:
 *   0       - 操作成功
 *   EAGAIN  - 需要更多数据
 *   EBADMSG - 报文格式错误
 */

#ifndef AHPARSER_AHP_H_
#define AHPARSER_AHP_H_

#include "parser.h"
#include "splitter.h"

#endif  // AHPARSER_AHP_H_
